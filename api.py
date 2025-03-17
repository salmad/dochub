from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import Dict, List, Optional, Annotated
from datetime import datetime
import google.generativeai as genai
from supabase import create_client, Client
import os
from dotenv import load_dotenv
import logging
import json
from fuzzywuzzy import fuzz

# Initialize FastAPI app
app = FastAPI(title="DocKeeper API", version="1.0.0")

# Configure CORS
allowed_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Load environment variables
load_dotenv()

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Security scheme
security = HTTPBearer()

# Initialize Supabase client
def get_supabase() -> Client:
    """Initialize and return Supabase client."""
    try:
        url = os.environ.get("SUPABASE_URL")
        key = os.environ.get("SUPABASE_KEY")
        if not url or not key:
            raise ValueError("Missing Supabase credentials")
        
        # Create client with default options
        client = create_client(url, key)
        return client
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        raise HTTPException(status_code=500, detail="Database connection failed")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> str:
    """Get current user from JWT token."""
    try:
        supabase = get_supabase()
        # Verify the JWT token
        user = supabase.auth.get_user(credentials.credentials)
        if not user or not user.user:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication credentials"
            )
        return user.user.id
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}")
        raise HTTPException(
            status_code=401,
            detail="Invalid authentication credentials"
        )

# Initialize Gemini AI
def get_gemini():
    """Initialize and return Gemini AI model."""
    try:
        api_key = os.getenv("GOOGLE_API_KEY")
        if not api_key:
            raise ValueError("Missing Google API key")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-1.5-flash')
    except Exception as e:
        logger.error(f"Failed to initialize Gemini AI: {str(e)}")
        raise HTTPException(status_code=500, detail="AI model initialization failed")

# Pydantic models for request/response validation
class UserAuth(BaseModel):
    email: str
    password: str

class UserResponse(BaseModel):
    id: str
    email: str

class DocumentResponse(BaseModel):
    id: str
    file_name: str
    document_type: str
    pdf_url: Optional[str]
    processed_at: str
    fields: Dict[str, str]

class SearchResult(BaseModel):
    field_name: str
    field_value: str
    document_name: str
    pdf_url: Optional[str]
    match_score: float

# Authentication endpoints
@app.get("/auth/me", response_model=UserResponse)
async def get_me(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        supabase = get_supabase()
        # Use the token directly to get user info
        user = supabase.auth.get_user(credentials.credentials)
        if not user or not user.user:
            raise HTTPException(status_code=404, detail="User not found")
        return {"id": user.user.id, "email": user.user.email}
    except Exception as e:
        logger.error(f"Get user error: {str(e)}")
        raise HTTPException(status_code=401, detail="Failed to get user info")

@app.post("/auth/login")
async def login(user_auth: UserAuth):
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_in_with_password({
            "email": user_auth.email,
            "password": user_auth.password
        })
        return {"user_id": response.user.id, "access_token": response.session.access_token}
    except Exception as e:
        logger.error(f"Login error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid credentials")

@app.post("/auth/signup")
async def signup(user_auth: UserAuth):
    try:
        supabase = get_supabase()
        response = supabase.auth.sign_up({
            "email": user_auth.email,
            "password": user_auth.password
        })
        return {"message": "Account created successfully"}
    except Exception as e:
        logger.error(f"Signup error: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))
    


# Document processing endpoints
@app.post("/documents/process")
async def process_document(
    file: UploadFile = File(...),
    user_id: str = Depends(get_current_user)):
    try:
        supabase = get_supabase()
        model = get_gemini()
        
        # Read PDF file
        pdf_bytes = await file.read()
        
        # Check if document exists
        existing = supabase.table('documents') \
            .select('*') \
            .eq('file_name', file.filename) \
            .eq('user_id', user_id) \
            .execute()
            
        if existing.data:
            raise HTTPException(status_code=400, detail="Document already exists")
        
        # Process with Gemini AI
        prompt = """
        Analyze this document and extract all possible information.
        Return the data in the following JSON format:
        {
            "fields": [           
                {
                    "field_name": "full_name",
                    "field_value": "JOHN DOE"
                },
                {
                    "field_name": "date_of_birth",
                    "field_value": "1990-01-01"
                }
            ],
            "document_type": "choose from passport, visa, driver's license, employer info, education, etc."
        }
        """
        
        image_parts = [{"mime_type": "application/pdf", "data": pdf_bytes}]
        response = model.generate_content([prompt, image_parts[0]])
        response.resolve()
        
        # Parse AI response
        json_str = response.text.strip()
        if json_str.startswith("```json"):
            json_str = json_str[7:-3]
        elif json_str.startswith("```"):
            json_str = json_str[3:-3]
        
        parsed_data = json.loads(json_str)
        extracted_data = {
            field['field_name'].strip(): str(field['field_value']).strip()
            for field in parsed_data.get('fields', [])
            if field.get('field_name') and field.get('field_value')
        }
        
        # Upload PDF to storage
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        storage_file_name = f"passports/{timestamp}_{file.filename}"
        
        supabase.storage \
            .from_("documents") \
            .upload(
                path=storage_file_name,
                file=pdf_bytes,
                file_options={"content-type": "application/pdf"}
            )
        
        pdf_url = supabase.storage \
            .from_("documents") \
            .get_public_url(storage_file_name)
        
        # Save document metadata
        document_data = {
            'user_id': user_id,
            'document_type': parsed_data['document_type'],
            'file_name': file.filename,
            'processed_at': datetime.utcnow().isoformat(),
            'pdf_url': pdf_url
        }
        
        doc_result = supabase.table('documents').insert(document_data).execute()
        document_id = doc_result.data[0]['id']
        
        # Save extracted fields
        data_points = [
            {
                'document_id': document_id,
                'user_id': user_id,
                'field_name': field_name,
                'field_value': field_value
            }
            for field_name, field_value in extracted_data.items()
        ]
        
        if data_points:
            supabase.table('data_points').insert(data_points).execute()
        
        return {
            "document_id": document_id,
            "fields": extracted_data,
            "pdf_url": pdf_url
        }
        
    except Exception as e:
        logger.error(f"Document processing error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents", response_model=List[DocumentResponse])
async def get_documents(user_id: str = Depends(get_current_user)):
    try:
        logger.info(f"Fetching documents for user: {user_id}")
        supabase = get_supabase()
        
        # Fetch documents
        documents = supabase.table('documents') \
            .select('*') \
            .eq('user_id', user_id) \
            .order('created_at', desc=True) \
            .execute()
        
        logger.info(f"Found {len(documents.data)} documents")
        
        # Fetch data points
        data_points = supabase.table('data_points') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
        
        logger.info(f"Found {len(data_points.data)} data points")
        
        # Organize data
        result = []
        for doc in documents.data:
            doc_fields = {
                point['field_name']: point['field_value']
                for point in data_points.data
                if point['document_id'] == doc['id']
            }
            
            result.append(DocumentResponse(
                id=doc['id'],
                file_name=doc['file_name'],
                document_type=doc['document_type'],
                pdf_url=doc.get('pdf_url'),
                processed_at=doc['processed_at'],
                fields=doc_fields
            ))
        
        logger.info(f"Returning {len(result)} processed documents")
        return result
        
    except Exception as e:
        logger.error(f"Error fetching documents: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/documents/search", response_model=List[SearchResult])
async def search_documents(
    query: str,
    min_score: int = 60,
    user_id: str = Depends(get_current_user)
):
    try:
        supabase = get_supabase()
        
        # Fetch user's documents and data points
        documents = supabase.table('documents') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
        
        data_points = supabase.table('data_points') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
        
        # Organize data for searching
        results = []
        for doc in documents.data:
            doc_fields = {
                point['field_name']: point['field_value']
                for point in data_points.data
                if point['document_id'] == doc['id']
            }
            
            for field_name, field_value in doc_fields.items():
                name_score = fuzz.partial_ratio(query.lower(), field_name.lower())
                value_score = fuzz.partial_ratio(query.lower(), str(field_value).lower())
                max_score = max(name_score, value_score)
                
                if max_score >= min_score:
                    results.append(SearchResult(
                        field_name=field_name,
                        field_value=field_value,
                        document_name=doc['file_name'],
                        pdf_url=doc.get('pdf_url'),
                        match_score=max_score
                    ))
        
        # Sort by match score
        results.sort(key=lambda x: x.match_score, reverse=True)
        return results
        
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/documents/categorize")
async def categorize_fields(user_id: str = Depends(get_current_user)):
    try:
        supabase = get_supabase()
        model = get_gemini()
        
        # Fetch all documents and their fields
        documents = supabase.table('documents') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
            
        data_points = supabase.table('data_points') \
            .select('*') \
            .eq('user_id', user_id) \
            .execute()
            
        # Organize fields
        all_fields = {}
        for doc in documents.data:
            doc_fields = {
                point['field_name']: point['field_value']
                for point in data_points.data
                if point['document_id'] == doc['id']
            }
            all_fields.update(doc_fields)
            
        if not all_fields:
            return {"categories": {}}
            
        # Prepare prompt for Gemini
        fields_json = json.dumps(all_fields, indent=2)
        prompt = """
        Analyze these fields and values and categorize them into logical groups.
        Fields and values to analyze:
        """ + fields_json + """

        Categorize them into these groups (only include relevant groups that have matching fields):
        - Personal Information (name, age, contact, etc.)
        - Education (degrees, schools, etc.)
        - Employment (work history, position, etc.)
        - Financial (income, accounts, etc.)
        - Identity Documents (passport numbers, IDs, etc.)
        - Other (anything that doesn't fit above)

        Return the categorized fields in this exact JSON format:
        {
            "categories": {
                "Personal Information": { "field_name": "value" },
                "Education": { "field_name": "value" },
                // ... other categories
            }
        }
        Only include categories that have matching fields. Format field names in a human-readable way.
        """
        
        response = model.generate_content(prompt)
        response.resolve()
        
        # Parse the response
        response_text = response.text.strip()
        # Extract JSON content from markdown code block if present
        if "```json" in response_text:
            response_text = response_text[response_text.find("```json") + 7:response_text.rfind("```")]
        elif "```" in response_text:
            response_text = response_text[response_text.find("```") + 3:response_text.rfind("```")]
        
        # Clean up any comments in the JSON
        response_text = "\n".join(
            line for line in response_text.split("\n")
            if not line.strip().startswith("//")
        )
        
        try:
            categorized_data = json.loads(response_text)
            # Ensure the response has the expected structure
            if not isinstance(categorized_data, dict) or "categories" not in categorized_data:
                categorized_data = {"categories": {}}
            return categorized_data
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {str(e)}")
            logger.error(f"Response text: {response_text}")
            return {"categories": {}}
        
    except Exception as e:
        logger.error(f"Categorization error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=8000) 