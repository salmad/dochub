import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import google.generativeai as genai
from supabase import Client
import streamlit as st
import sys
import os

# Add the parent directory to the Python path to import app.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app import (
    setup_logging,
    init_supabase,
    init_gemini,
    process_with_gemini,
    check_document_exists,
    upload_pdf_to_storage,
    save_to_supabase,
    fetch_all_documents,
    get_current_user
)

# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def mock_supabase():
    """Mock Supabase client with common methods."""
    mock = Mock(spec=Client)
    
    # Mock table operations
    mock_table = Mock()
    mock_table.select.return_value = mock_table
    mock_table.eq.return_value = mock_table
    mock_table.order.return_value = mock_table
    mock_table.execute.return_value = Mock(data=[])
    mock.table.return_value = mock_table
    
    # Mock storage operations
    mock_storage = Mock()
    mock_storage.from_.return_value = mock_storage
    mock_storage.upload.return_value = {"Key": "test.pdf"}
    mock_storage.get_public_url.return_value = "https://test-url.com/test.pdf"
    mock.storage = mock_storage
    
    # Mock auth operations
    mock_auth = Mock()
    mock_auth.get_user.return_value = Mock(id='test-user-id')
    mock.auth = mock_auth
    
    return mock

@pytest.fixture
def mock_user():
    """Mock authenticated user data."""
    return {
        'id': 'test-user-id',
        'email': 'test@example.com'
    }

@pytest.fixture
def mock_gemini():
    """Mock Gemini AI model."""
    mock = Mock()
    mock_response = Mock()
    mock_response.text = '''
    {
        "fields": [
            {
                "field_name": "full_name",
                "field_value": "John Doe"
            },
            {
                "field_name": "date_of_birth",
                "field_value": "1990-01-01"
            }
        ]
    }
    '''
    mock.generate_content.return_value = mock_response
    return mock

@pytest.fixture
def sample_pdf_bytes():
    """Sample PDF bytes for testing."""
    return b'%PDF-1.4 test pdf content'

@pytest.fixture
def sample_document_data():
    """Sample document data for testing."""
    return {
        'full_name': 'John Doe',
        'date_of_birth': '1990-01-01',
        'passport_number': 'AB123456'
    }

# ============================================================================
# Configuration Tests
# ============================================================================

def test_setup_logging():
    """Test logging configuration."""
    logger = setup_logging()
    assert logger.level == 20  # INFO level
    assert len(logger.handlers) == 2  # File and stdout handlers

@patch('app.create_client')
def test_init_supabase_success(mock_create_client, mock_supabase):
    """Test successful Supabase initialization."""
    mock_create_client.return_value = mock_supabase
    
    with patch.dict('os.environ', {'SUPABASE_URL': 'test_url', 'SUPABASE_KEY': 'test_key'}):
        client = init_supabase()
        assert client is not None
        mock_create_client.assert_called_once_with('test_url', 'test_key')

@patch('app.create_client')
def test_init_supabase_failure(mock_create_client):
    """Test Supabase initialization failure."""
    mock_create_client.side_effect = Exception("Connection failed")
    
    with patch.dict('os.environ', {'SUPABASE_URL': 'test_url', 'SUPABASE_KEY': 'test_key'}):
        client = init_supabase()
        assert client is None

def test_init_gemini_success():
    """Test successful Gemini AI initialization."""
    with patch.dict('os.environ', {'GOOGLE_API_KEY': 'test_key'}):
        with patch('google.generativeai.configure') as mock_configure:
            with patch('google.generativeai.GenerativeModel') as mock_model:
                mock_model.return_value = Mock()
                model = init_gemini()
                assert model is not None
                mock_configure.assert_called_once_with(api_key='test_key')

# ============================================================================
# AI Processing Tests
# ============================================================================

def test_process_with_gemini_success(mock_gemini, sample_pdf_bytes):
    """Test successful PDF processing with Gemini AI."""
    with patch('app.model', mock_gemini):
        result = process_with_gemini(sample_pdf_bytes)
        
        assert result is not None
        assert isinstance(result, dict)
        assert result['full_name'] == 'John Doe'
        assert result['date_of_birth'] == '1990-01-01'
        
        mock_gemini.generate_content.assert_called_once()

def test_process_with_gemini_invalid_response(mock_gemini, sample_pdf_bytes):
    """Test Gemini AI processing with invalid JSON response."""
    mock_gemini.generate_content.return_value.text = 'Invalid JSON'
    
    with patch('app.model', mock_gemini):
        result = process_with_gemini(sample_pdf_bytes)
        assert result is None

# ============================================================================
# Storage Tests
# ============================================================================

def test_check_document_exists_true(mock_supabase):
    """Test checking for existing document (found)."""
    mock_supabase.table().execute.return_value.data = [{'id': 1}]
    
    with patch('app.supabase', mock_supabase):
        result = check_document_exists('test.pdf')
        assert result is True

def test_check_document_exists_false(mock_supabase):
    """Test checking for existing document (not found)."""
    mock_supabase.table().execute.return_value.data = []
    
    with patch('app.supabase', mock_supabase):
        result = check_document_exists('test.pdf')
        assert result is False

def test_upload_pdf_to_storage_success(mock_supabase, sample_pdf_bytes):
    """Test successful PDF upload to storage."""
    with patch('app.supabase', mock_supabase):
        result = upload_pdf_to_storage(sample_pdf_bytes, 'test.pdf')
        
        assert result == 'https://test-url.com/test.pdf'
        mock_supabase.storage.from_.assert_called_once_with('documents')

def test_upload_pdf_to_storage_failure(mock_supabase, sample_pdf_bytes):
    """Test PDF upload failure."""
    mock_supabase.storage.from_().upload.side_effect = Exception('Upload failed')
    
    with patch('app.supabase', mock_supabase):
        result = upload_pdf_to_storage(sample_pdf_bytes, 'test.pdf')
        assert result is None

# ============================================================================
# Authentication Tests
# ============================================================================

def test_get_current_user_success(mock_supabase):
    """Test successful current user retrieval."""
    with patch('app.supabase', mock_supabase):
        user_id = get_current_user()
        assert user_id == 'test-user-id'
        mock_supabase.auth.get_user.assert_called_once()

def test_get_current_user_failure(mock_supabase):
    """Test current user retrieval failure."""
    mock_supabase.auth.get_user.side_effect = Exception("Auth error")
    
    with patch('app.supabase', mock_supabase):
        user_id = get_current_user()
        assert user_id is None

def test_get_current_user_not_authenticated(mock_supabase):
    """Test current user retrieval when not authenticated."""
    mock_supabase.auth.get_user.return_value = None
    
    with patch('app.supabase', mock_supabase):
        user_id = get_current_user()
        assert user_id is None

# ============================================================================
# Database Operation Tests
# ============================================================================

def test_save_to_supabase_success(mock_supabase, sample_pdf_bytes, sample_document_data):
    """Test successful document save to Supabase."""
    mock_supabase.table().execute.return_value.data = []  # Document doesn't exist
    mock_supabase.table().insert().execute.return_value.data = [{'id': 'test-id'}]
    
    with patch('app.supabase', mock_supabase):
        result = save_to_supabase(sample_document_data, 'test.pdf', sample_pdf_bytes)
        
        assert result == 'test-id'
        mock_supabase.table.assert_any_call('documents')
        mock_supabase.table.assert_any_call('data_points')

def test_save_to_supabase_existing_document(mock_supabase, sample_pdf_bytes, sample_document_data):
    """Test save attempt with existing document."""
    mock_supabase.table().execute.return_value.data = [{'id': 1}]  # Document exists
    
    with patch('app.supabase', mock_supabase):
        result = save_to_supabase(sample_document_data, 'test.pdf', sample_pdf_bytes)
        assert result is None

def test_check_document_exists_with_user(mock_supabase, mock_user):
    """Test document existence check with user context."""
    mock_supabase.table().execute.return_value.data = [{'id': 1}]
    
    with patch('app.supabase', mock_supabase):
        result = check_document_exists('test.pdf')
        assert result is True
        
        # Verify user_id was included in the query
        mock_supabase.table().eq.assert_any_call('user_id', mock_user['id'])

def test_save_to_supabase_with_user(mock_supabase, mock_user, sample_pdf_bytes, sample_document_data):
    """Test document save with user context."""
    mock_supabase.table().execute.return_value.data = []  # Document doesn't exist
    mock_supabase.table().insert().execute.return_value.data = [{'id': 'test-id'}]
    
    with patch('app.supabase', mock_supabase):
        result = save_to_supabase(sample_document_data, 'test.pdf', sample_pdf_bytes)
        
        assert result == 'test-id'
        
        # Verify user_id was included in document data
        insert_call_args = mock_supabase.table().insert.call_args[0][0]
        assert insert_call_args['user_id'] == mock_user['id']

def test_fetch_all_documents_success(mock_supabase):
    """Test successful document fetch."""
    mock_documents = [
        {'id': '1', 'file_name': 'test1.pdf', 'document_type': 'passport'},
        {'id': '2', 'file_name': 'test2.pdf', 'document_type': 'passport'}
    ]
    mock_data_points = [
        {'document_id': '1', 'field_name': 'full_name', 'field_value': 'John Doe'},
        {'document_id': '1', 'field_name': 'date_of_birth', 'field_value': '1990-01-01'}
    ]
    
    mock_supabase.table().execute.side_effect = [
        Mock(data=mock_documents),
        Mock(data=mock_data_points)
    ]
    
    with patch('app.supabase', mock_supabase):
        result = fetch_all_documents()
        
        assert result is not None
        assert len(result) == 2
        assert 'fields' in result['1']
        assert result['1']['fields']['full_name'] == 'John Doe'

def test_fetch_all_documents_failure(mock_supabase):
    """Test document fetch failure."""
    mock_supabase.table().execute.side_effect = Exception('Database error')
    
    with patch('app.supabase', mock_supabase):
        result = fetch_all_documents()
        assert result is None

def test_fetch_all_documents_with_user(mock_supabase, mock_user):
    """Test document fetch with user context."""
    mock_documents = [
        {'id': '1', 'file_name': 'test1.pdf', 'user_id': mock_user['id']},
        {'id': '2', 'file_name': 'test2.pdf', 'user_id': mock_user['id']}
    ]
    mock_data_points = [
        {'document_id': '1', 'field_name': 'full_name', 'field_value': 'John Doe', 'user_id': mock_user['id']},
        {'document_id': '1', 'field_name': 'date_of_birth', 'field_value': '1990-01-01', 'user_id': mock_user['id']}
    ]
    
    mock_supabase.table().execute.side_effect = [
        Mock(data=mock_documents),
        Mock(data=mock_data_points)
    ]
    
    with patch('app.supabase', mock_supabase):
        result = fetch_all_documents()
        
        assert result is not None
        assert len(result) == 2
        
        # Verify user_id filter was applied
        mock_supabase.table().eq.assert_any_call('user_id', mock_user['id'])

def test_fetch_all_documents_no_user(mock_supabase):
    """Test document fetch without authenticated user."""
    mock_supabase.auth.get_user.return_value = None
    
    with patch('app.supabase', mock_supabase):
        result = fetch_all_documents()
        assert result is None

# ============================================================================
# Integration Tests
# ============================================================================

def test_full_document_processing_flow(mock_supabase, mock_gemini, sample_pdf_bytes):
    """Test the complete document processing flow."""
    # Setup mocks
    mock_supabase.table().execute.return_value.data = []  # Document doesn't exist
    mock_supabase.table().insert().execute.return_value.data = [{'id': 'test-id'}]
    
    with patch('app.supabase', mock_supabase), patch('app.model', mock_gemini):
        # Process document
        extracted_data = process_with_gemini(sample_pdf_bytes)
        assert extracted_data is not None
        
        # Save to database
        document_id = save_to_supabase(extracted_data, 'test.pdf', sample_pdf_bytes)
        assert document_id == 'test-id'
        
        # Verify storage and database calls
        mock_supabase.storage.from_.assert_called_with('documents')
        mock_supabase.table.assert_any_call('documents')
        mock_supabase.table.assert_any_call('data_points') 