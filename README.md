# DocKeeper Application

A modern document management system that extracts and categorizes information from PDF documents using AI.

## Features

- PDF document upload and processing
- Automatic field extraction
- AI-powered field categorization using Google's Gemini
- Search functionality across all documents
- Modern, responsive UI built with Next.js and Tailwind CSS
- Secure authentication system

## Tech Stack

### Frontend
- Next.js 13+
- React
- Tailwind CSS
- Shadcn UI Components
- TypeScript

### Backend
- FastAPI
- Supabase (PostgreSQL + Authentication)
- Google Gemini AI
- Python 3.8+

## Getting Started

### Prerequisites
- Node.js 16+
- Python 3.8+
- Supabase account
- Google Cloud account (for Gemini AI)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/dockeeper.git
cd dockeeper
```

2. Frontend setup:
```bash
cd dockeeper-web
npm install
cp .env.example .env.local
# Update .env.local with your configuration
npm run dev
```

3. Backend setup:
```bash
cd ../backend
python -m venv env
source env/bin/activate  # On Windows: .\env\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
# Update .env with your configuration
uvicorn api:app --reload
```

## Environment Variables

### Frontend (.env.local)
```
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### Backend (.env)
```
DATABASE_URL=your-supabase-postgres-url
SUPABASE_URL=your-supabase-project-url
SUPABASE_KEY=your-supabase-service-key
GOOGLE_API_KEY=your-gemini-api-key
CORS_ORIGINS=http://localhost:3000
```

## Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [Shadcn UI](https://ui.shadcn.com/) for the beautiful UI components
- [Google Gemini AI](https://deepmind.google/technologies/gemini/) for document analysis
- [Supabase](https://supabase.com/) for backend infrastructure
