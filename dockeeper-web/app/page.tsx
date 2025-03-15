'use client'

import { useState, useEffect } from 'react'
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger } from "@/components/ui/dropdown-menu"
import { Upload, Search, LogOut, Loader2, User, Plus, Mail, Phone, Hash, Type, Check, Copy, Sparkles, UserCircle, GraduationCap, Briefcase, Wallet, FileKey, Files } from "lucide-react"
import { useAuth } from '@/lib/auth-context'
import * as api from '@/lib/api'

interface Document {
  id: string
  file_name: string
  document_type: string
  pdf_url?: string
  processed_at: string
  fields: Record<string, string>
}

interface SearchResult {
  field_name: string
  field_value: string
  document_name: string
  pdf_url?: string
}

interface CategorizedData {
  categories: {
    [key: string]: {
      [field: string]: string
    }
  }
}

function getFieldIcon(fieldName: string, value: string) {
  // Check for email
  if (fieldName.toLowerCase().includes('email') || value.includes('@')) {
    return <Mail className="w-4 h-4" />
  }
  // Check for phone
  if (fieldName.toLowerCase().includes('phone') || /^[\d\s\-\+\(\)]+$/.test(value)) {
    return <Phone className="w-4 h-4" />
  }
  // Check for numbers
  if (!isNaN(Number(value))) {
    return <Hash className="w-4 h-4" />
  }
  // Default to text
  return <Type className="w-4 h-4" />
}

function CopyableValue({ value }: { value: string }) {
  const [copied, setCopied] = useState(false)

  const handleCopy = () => {
    navigator.clipboard.writeText(value)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <div className="flex items-center gap-2 group">
      <span>{value}</span>
      <Button
        variant="ghost"
        size="sm"
        className="opacity-0 group-hover:opacity-100 transition-opacity"
        onClick={handleCopy}
      >
        {copied ? (
          <Check className="w-4 h-4 text-green-500" />
        ) : (
          <Copy className="w-4 h-4" />
        )}
        <span className="sr-only">Copy value</span>
      </Button>
    </div>
  )
}

function getCategoryIcon(category: string) {
  // Common colors for all categories
  const colors = {
    color: 'bg-slate-50/90',
    hoverColor: 'hover:bg-slate-100/90',
    textColor: 'text-slate-700'
  }

  // Only icons differ by category
  switch (category.toLowerCase()) {
    case 'personal information':
      return { 
        icon: <UserCircle className="w-5 h-5 text-slate-600" />,
        ...colors
      }
    case 'education':
      return { 
        icon: <GraduationCap className="w-5 h-5 text-slate-600" />,
        ...colors
      }
    case 'employment':
      return { 
        icon: <Briefcase className="w-5 h-5 text-slate-600" />,
        ...colors
      }
    case 'financial':
      return { 
        icon: <Wallet className="w-5 h-5 text-slate-600" />,
        ...colors
      }
    case 'identity documents':
      return { 
        icon: <FileKey className="w-5 h-5 text-slate-600" />,
        ...colors
      }
    default:
      return { 
        icon: <Files className="w-5 h-5 text-slate-600" />,
        ...colors
      }
  }
}

export default function Home() {
  const { isAuthenticated, token, login, signup, logout } = useAuth();
  const [searchTerm, setSearchTerm] = useState('')
  const [searchResults, setSearchResults] = useState<SearchResult[]>([])
  const [documents, setDocuments] = useState<Document[]>([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [categorizedFields, setCategorizedFields] = useState<CategorizedData>({ categories: {} })
  const [expandedCategories, setExpandedCategories] = useState<Record<string, boolean>>({})

  const toggleCategory = (category: string) => {
    setExpandedCategories(prev => ({
      ...prev,
      [category]: !prev[category]
    }))
  }

  useEffect(() => {
    if (isAuthenticated && token) {
      fetchDocuments()
      fetchCategorizedFields()
    }
  }, [isAuthenticated, token])

  const handleLoginSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const form = e.target as HTMLFormElement
    const email = (form.elements.namedItem('email') as HTMLInputElement).value
    const password = (form.elements.namedItem('password') as HTMLInputElement).value

    try {
      await login(email, password)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleSignupSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    setError('')
    setIsLoading(true)

    const form = e.target as HTMLFormElement
    const email = (form.elements.namedItem('email') as HTMLInputElement).value
    const password = (form.elements.namedItem('password') as HTMLInputElement).value

    try {
      await signup(email, password)
    } catch (error: any) {
      setError(error.message)
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileUpload = async (file: File) => {
    try {
      if (!token) throw new Error('Not authenticated')
      await api.processDocument(file, token)
      fetchDocuments()
    } catch (error: any) {
      setError(error.message)
    }
  }

  const fetchDocuments = async () => {
    try {
      if (!token) throw new Error('Not authenticated')
      const data = await api.getDocuments(token)
      setDocuments(data)
    } catch (error: any) {
      setError(error.message)
    }
  }

  const handleSearch = async () => {
    try {
      if (!token) throw new Error('Not authenticated')
      const data = await api.searchDocuments(searchTerm, token)
      setSearchResults(data)
    } catch (error: any) {
      setError(error.message)
    }
  }

  const fetchCategorizedFields = async () => {
    try {
      if (!token) throw new Error('Not authenticated')
      const data = await api.getCategorizedFields(token)
      setCategorizedFields(data)
    } catch (error: any) {
      setError(error.message)
    }
  }

  if (!isAuthenticated) {
  return (
      <div className="container mx-auto p-4">
        <Card>
          <CardHeader>
            <CardTitle>Welcome to DocKeeper</CardTitle>
            <CardDescription>Please login or signup to continue</CardDescription>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="login">
              <TabsList className="grid w-full grid-cols-2">
                <TabsTrigger value="login">Login</TabsTrigger>
                <TabsTrigger value="signup">Signup</TabsTrigger>
              </TabsList>
              <TabsContent value="login">
                <form onSubmit={handleLoginSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Input
                      name="email"
                      type="email"
                      placeholder="Email"
                      required
                      disabled={isLoading}
                    />
                    <Input
                      name="password"
                      type="password"
                      placeholder="Password"
                      required
                      disabled={isLoading}
                    />
        </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Logging in...
                      </>
                    ) : (
                      'Login'
                    )}
                  </Button>
                </form>
              </TabsContent>
              <TabsContent value="signup">
                <form onSubmit={handleSignupSubmit} className="space-y-4">
                  <div className="space-y-2">
                    <Input
                      name="email"
                      type="email"
                      placeholder="Email"
                      required
                      disabled={isLoading}
                    />
                    <Input
                      name="password"
                      type="password"
                      placeholder="Password"
                      required
                      disabled={isLoading}
                    />
                  </div>
                  <Button type="submit" className="w-full" disabled={isLoading}>
                    {isLoading ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Signing up...
                      </>
                    ) : (
                      'Sign up'
                    )}
                  </Button>
                </form>
              </TabsContent>
            </Tabs>
            {error && (
              <Alert variant="destructive" className="mt-4">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}
          </CardContent>
        </Card>
      </div>
    )
  }

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-2xl font-bold mb-1">Docpads</h1>
          <p className="text-muted-foreground">Manage your documents and access your information easily</p>
        </div>
        <div className="flex items-center gap-2">
          <Sheet>
            <SheetTrigger asChild>
              <Button variant="default">
                <Plus className="w-4 h-4 mr-2" />
                Upload Source
              </Button>
            </SheetTrigger>
            <SheetContent>
              <SheetHeader>
                <SheetTitle>Upload Source</SheetTitle>
                <SheetDescription>Choose a PDF file to upload</SheetDescription>
              </SheetHeader>
              <div className="mt-4">
                <Input
                  type="file"
                  accept=".pdf"
                  onChange={(e) => {
                    const file = e.target.files?.[0]
                    if (file) handleFileUpload(file)
                  }}
                />
              </div>
            </SheetContent>
          </Sheet>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="rounded-full">
                <User className="w-5 h-5" />
                <span className="sr-only">Open profile menu</span>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={logout}>
                <LogOut className="w-4 h-4 mr-2" />
                Logout
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      <div className="mb-6">
        <div className="max-w-md">
          <div className="flex gap-2">
            <Input
              placeholder="Search documents..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
            />
            <Button onClick={handleSearch}>
              <Search className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {error && (
        <Alert className="mb-6">
          <AlertDescription>{error}</AlertDescription>
        </Alert>
      )}

      <div className="mt-4">
        <Tabs defaultValue="documents">
          <TabsList>
            <TabsTrigger value="documents">My Sources</TabsTrigger>
            <TabsTrigger value="search">Extracted Info</TabsTrigger>
            <TabsTrigger value="categories" className="flex items-center gap-2">
              Categorized
              <Sparkles className="w-4 h-4 text-yellow-500" />
            </TabsTrigger>
          </TabsList>
          <TabsContent value="documents">
            <div className="rounded-md border">
              <div className="grid grid-cols-5 gap-4 p-4 bg-muted/50 font-medium">
                <div>Name</div>
                <div>Type</div>
                <div>Date</div>
                <div>Size</div>
                <div>Actions</div>
              </div>
              <div className="divide-y">
                {documents.map((doc: any) => (
                  <div key={doc.id} className="grid grid-cols-5 gap-4 p-4 items-center hover:bg-muted/50">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 bg-muted rounded flex items-center justify-center">
                        {doc.document_type === 'passport' ? '🛂' : '📄'}
                      </div>
                      <span>{doc.file_name}</span>
                    </div>
                    <div className="capitalize">{doc.document_type}</div>
                    <div>{new Date(doc.processed_at).toLocaleDateString()}</div>
                    <div>-</div>
                    <div className="flex items-center gap-2">
                      {doc.pdf_url && (
                        <Button variant="ghost" size="sm" asChild>
                          <a href={doc.pdf_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                            <span className="sr-only">View</span>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                          </a>
                        </Button>
                      )}
                      <Button variant="ghost" size="sm">
                        <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="1"/><circle cx="19" cy="12" r="1"/><circle cx="5" cy="12" r="1"/></svg>
                        <span className="sr-only">More</span>
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="search">
            <div className="rounded-md border">
              <div className="grid grid-cols-4 gap-4 p-4 bg-muted/50 font-medium">
                <div>Field</div>
                <div>Value</div>
                <div>Source</div>
                <div>Actions</div>
              </div>
              <div className="divide-y">
                {(searchTerm ? searchResults : documents.flatMap(doc => 
                  Object.entries(doc.fields || {}).map(([field_name, field_value]) => ({
                    field_name,
                    field_value,
                    document_name: doc.file_name,
                    pdf_url: doc.pdf_url
                  }))
                )).map((result: any, index: number) => (
                  <div key={`${result.document_name}-${result.field_name}-${index}`} 
                       className="grid grid-cols-4 gap-4 p-4 items-center hover:bg-muted/50">
                    <div className="flex items-center gap-2">
                      {getFieldIcon(result.field_name, result.field_value)}
                      <span className="font-medium">{result.field_name}</span>
                    </div>
                    <CopyableValue value={result.field_value} />
                    <div className="text-muted-foreground">{result.document_name}</div>
                    <div className="flex items-center gap-2">
                      {result.pdf_url && (
                        <Button variant="ghost" size="sm" asChild>
                          <a href={result.pdf_url} target="_blank" rel="noopener noreferrer" className="flex items-center gap-2">
                            <span className="sr-only">View Source</span>
                            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
                          </a>
                        </Button>
                      )}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="categories">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">AI-Powered Categories</h2>
              <Button 
                variant="outline" 
                size="sm"
                onClick={fetchCategorizedFields}
                disabled={isLoading}
                className="flex items-center gap-2"
              >
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 animate-spin" />
                    Categorizing...
                  </>
                ) : (
                  <>
                    <svg
                      xmlns="http://www.w3.org/2000/svg"
                      width="16"
                      height="16"
                      viewBox="0 0 24 24"
                      fill="none"
                      stroke="currentColor"
                      strokeWidth="2"
                      strokeLinecap="round"
                      strokeLinejoin="round"
                      className="h-4 w-4"
                    >
                      <path d="M3 12a9 9 0 0 1 9-9 9.75 9.75 0 0 1 6.74 2.74L21 8" />
                      <path d="M21 3v5h-5" />
                      <path d="M21 12a9 9 0 0 1-9 9 9.75 9.75 0 0 1-6.74-2.74L3 16" />
                      <path d="M8 16H3v5" />
                    </svg>
                    Refresh Categories
                  </>
                )}
              </Button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Object.entries(categorizedFields.categories).map(([category, fields]) => {
                const fieldCount = Object.keys(fields).length;
                const isExpanded = expandedCategories[category] || false;
                const iconData = getCategoryIcon(category);
                
                return (
                  <Card 
                    key={category} 
                    className={`transition-all duration-200 hover:shadow-md border-none ${iconData.color} ${iconData.hoverColor}`}
                  >
                    <CardHeader 
                      className="cursor-pointer space-y-3" 
                      onClick={() => toggleCategory(category)}
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          {iconData.icon}
                          <CardTitle className={`text-base ${iconData.textColor}`}>{category}</CardTitle>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className={`text-sm ${iconData.textColor}`}>
                            {fieldCount} {fieldCount === 1 ? 'field' : 'fields'}
                          </span>
                          <Button variant="ghost" size="sm" className={iconData.hoverColor}>
                            <svg
                              xmlns="http://www.w3.org/2000/svg"
                              width="16"
                              height="16"
                              viewBox="0 0 24 24"
                              fill="none"
                              stroke="currentColor"
                              strokeWidth="2"
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              className={`h-4 w-4 transition-transform duration-200 ${isExpanded ? 'rotate-180' : ''} ${iconData.textColor}`}
                            >
                              <path d="m6 9 6 6 6-6"/>
                            </svg>
                          </Button>
                        </div>
                      </div>
                      {!isExpanded && (
                        <div className="flex flex-wrap gap-2">
                          {Object.entries(fields).slice(0, 3).map(([field]) => (
                            <div
                              key={field}
                              className={`bg-white/20 px-2 py-1 rounded-md text-sm ${iconData.textColor}`}
                            >
                              {field}
                            </div>
                          ))}
                          {Object.keys(fields).length > 3 && (
                            <div className={`bg-white/20 px-2 py-1 rounded-md text-sm ${iconData.textColor}`}>
                              +{Object.keys(fields).length - 3} more
                            </div>
                          )}
                        </div>
                      )}
                    </CardHeader>
                    {isExpanded && (
                      <CardContent>
                        <div className="rounded-md">
                          <div className="divide-y divide-white/10">
                            {Object.entries(fields).map(([field, value]) => (
                              <div key={field} className={`p-3 ${iconData.hoverColor}`}>
                                <div className="flex items-center gap-2 mb-1">
                                  {getFieldIcon(field, value)}
                                  <span className={`font-medium ${iconData.textColor}`}>{field}</span>
                                </div>
                                <CopyableValue value={value} />
                              </div>
                            ))}
                          </div>
                        </div>
                      </CardContent>
                    )}
                  </Card>
                );
              })}
              {Object.keys(categorizedFields.categories).length === 0 && (
                <div className="col-span-full text-center text-muted-foreground py-8">
                  No categorized fields available yet. Upload some documents to see AI-powered categorization.
                </div>
              )}
            </div>
          </TabsContent>
        </Tabs>
      </div>
    </div>
  )
}
