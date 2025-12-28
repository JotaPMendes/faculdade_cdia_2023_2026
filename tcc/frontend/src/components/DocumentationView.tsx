import { useState, useEffect } from 'react'
import axios from 'axios'
import { FileText, Book, Code, Archive } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import { cn } from '../utils/cn'

export default function DocumentationView() {
    const [activeDoc, setActiveDoc] = useState('readme')
    const [content, setContent] = useState('')
    const [loading, setLoading] = useState(false)

    const docs = [
        { id: 'readme', label: 'Project Overview', icon: Book },
        { id: 'architecture', label: 'Architecture', icon: Code },
        { id: 'learnings', label: 'Learnings & Logs', icon: FileText },
        { id: 'old_docs', label: 'Legacy Docs', icon: Archive },
    ]

    useEffect(() => {
        fetchDoc(activeDoc)
    }, [activeDoc])

    const fetchDoc = async (id: string) => {
        setLoading(true)
        try {
            const res = await axios.get(`http://localhost:8000/docs/${id}`)
            setContent(res.data.content)
        } catch (error) {
            setContent("Error loading documentation.")
        } finally {
            setLoading(false)
        }
    }

    return (
        <div className="flex h-full">
            {/* Doc Sidebar */}
            <div className="w-64 border-r border-border bg-card p-4 space-y-2">
                <h2 className="text-lg font-bold text-foreground mb-4 px-2">Documentation</h2>
                {docs.map(doc => (
                    <button
                        key={doc.id}
                        onClick={() => setActiveDoc(doc.id)}
                        className={cn(
                            "w-full flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                            activeDoc === doc.id
                                ? "bg-primary/10 text-primary border border-primary/20"
                                : "text-muted-foreground hover:bg-secondary hover:text-foreground"
                        )}
                    >
                        <doc.icon size={16} />
                        {doc.label}
                    </button>
                ))}
            </div>

            {/* Content */}
            <div className="flex-1 overflow-auto p-8 bg-background">
                <div className="max-w-4xl mx-auto">
                    {loading ? (
                        <div className="text-muted-foreground">Loading...</div>
                    ) : (
                        <div className="prose prose-slate dark:prose-invert max-w-none">
                            <ReactMarkdown>{content}</ReactMarkdown>
                        </div>
                    )}
                </div>
            </div>
        </div>
    )
}
