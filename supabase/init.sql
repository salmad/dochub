-- Create documents table to store document metadata
create table if not exists public.documents (
    id uuid default gen_random_uuid() primary key,
    user_id uuid references auth.users(id),
    document_type text not null,
    file_name text,
    pdf_url text,
    processed_at timestamp with time zone default timezone('utc'::text, now()),
    created_at timestamp with time zone default timezone('utc'::text, now())
);

-- Create data_points table to store extracted fields
create table if not exists public.data_points (
    id uuid default gen_random_uuid() primary key,
    document_id uuid references public.documents(id),
    user_id uuid references auth.users(id),
    field_name text not null,
    field_value text,
    created_at timestamp with time zone default timezone('utc'::text, now()),
    constraint fk_document
        foreign key (document_id)
        references documents(id)
        on delete cascade
);

-- Create users table to store user information
do $$
begin
    if not exists (select from pg_tables where schemaname = 'public' and tablename = 'users') then
        create table public.users (
            id uuid default gen_random_uuid() primary key,
            email text not null unique,
            password text not null,
            created_at timestamp with time zone default timezone('utc'::text, now())
        );
        
        create index idx_users_email on public.users(email);
        alter table public.users enable row level security;
        
        create policy "Users can insert their own users"
            on public.users
            for insert
            with check (auth.role() = 'authenticated');

        create policy "Users can view their own users"
            on public.users
            for select
            using (auth.role() = 'authenticated');
    end if;
end $$;

-- Create indexes for better query performance
create index idx_data_points_document_id on public.data_points(document_id);
create index idx_data_points_field_name on public.data_points(field_name);
create index idx_documents_user_id on public.documents(user_id);

-- Enable Row Level Security (RLS)
alter table public.documents enable row level security;
alter table public.data_points enable row level security;

-- Add user_id column to documents table if it doesn't exist
do $$
begin
    if not exists (select from information_schema.columns 
                  where table_schema = 'public' 
                  and table_name = 'documents' 
                  and column_name = 'user_id') then
        alter table public.documents 
        add column user_id uuid references auth.users(id);
        
        create index idx_documents_user_id on public.documents(user_id);
    end if;
end $$;

-- Add pdf_url column to documents table if it doesn't exist
do $$
begin
    if not exists (select from information_schema.columns 
                  where table_schema = 'public' 
                  and table_name = 'documents' 
                  and column_name = 'pdf_url') then
        alter table public.documents 
        add column pdf_url text;
    end if;
end $$;

-- Add user_id column to data_points table if it doesn't exist
do $$
begin
    if not exists (select from information_schema.columns 
                  where table_schema = 'public' 
                  and table_name = 'data_points' 
                  and column_name = 'user_id') then
        alter table public.data_points 
        add column user_id uuid references auth.users(id);
        
        create index idx_data_points_user_id on public.data_points(user_id);
    end if;
end $$;

-- Drop existing RLS policies if they exist and create new ones
do $$
begin
    -- Drop existing policies
    drop policy if exists "Users can insert their own documents" on public.documents;
    drop policy if exists "Users can view their own documents" on public.documents;
    drop policy if exists "Users can insert their own data points" on public.data_points;
    drop policy if exists "Users can view their own data points" on public.data_points;
    
    -- Create new policies
    create policy "Users can insert their own documents"
        on public.documents
        for insert
        with check (auth.uid() = user_id);

    create policy "Users can view their own documents"
        on public.documents
        for select
        using (auth.uid() = user_id);

    create policy "Users can insert their own data points"
        on public.data_points
        for insert
        with check (auth.uid() = user_id);

    create policy "Users can view their own data points"
        on public.data_points
        for select
        using (auth.uid() = user_id);
end $$;
