import { useState, useEffect } from 'react'
import axios from 'axios'
import { Trash2, Activity, Clock, FileText } from 'lucide-react'
import { cn } from '../utils/cn'

export default function ResultsView() {
    const [runs, setRuns] = useState<any[]>([])
    const [selectedRun, setSelectedRun] = useState<string | null>(null)
    const [runDetails, setRunDetails] = useState<any>(null)
    const [showDetails, setShowDetails] = useState(false)

    useEffect(() => {
        fetchRuns()
        const interval = setInterval(() => {
            fetchRuns()
        }, 5000)
        return () => clearInterval(interval)
    }, [selectedRun])

    useEffect(() => {
        if (selectedRun) {
            fetchRunDetails(selectedRun)
        }
    }, [selectedRun])

    const fetchRuns = async () => {
        try {
            const res = await axios.get('http://localhost:8000/runs')
            setRuns(res.data)
            setSelectedRun((currentSelectedRun) => {
                if (res.data.length === 0) return null
                if (currentSelectedRun && res.data.some((run: any) => run.id === currentSelectedRun)) {
                    return currentSelectedRun
                }
                return res.data[0].id
            })
        } catch (error) {
            console.error("Failed to fetch runs", error)
        }
    }

    const fetchRunDetails = async (runId: string) => {
        try {
            const res = await axios.get(`http://localhost:8000/runs/${runId}`)
            setRunDetails(res.data)
        } catch (error) {
            console.error("Failed to fetch run details", error)
        }
    }

    const renderKeyValueList = (data: Record<string, any> | undefined) => {
        if (!data || Object.keys(data).length === 0) {
            return <p className="text-sm text-muted-foreground">No data available.</p>
        }

        return (
            <dl className="space-y-2">
                {Object.entries(data).map(([key, value]) => (
                    <div key={key} className="grid grid-cols-[140px_1fr] gap-3 rounded-md border border-border/60 bg-background/40 px-3 py-2">
                        <dt className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">{key}</dt>
                        <dd className="text-sm text-foreground break-words font-mono">
                            {typeof value === 'object' && value !== null
                                ? JSON.stringify(value, null, 2)
                                : String(value)}
                        </dd>
                    </div>
                ))}
            </dl>
        )
    }

    const deleteRun = async (runId: string, e: React.MouseEvent) => {
        e.stopPropagation()
        if (!confirm(`Delete run ${runId}?`)) return

        try {
            await axios.delete(`http://localhost:8000/runs/${runId}`)
            fetchRuns()
            if (selectedRun === runId) setSelectedRun(null)
        } catch (error) {
            alert("Failed to delete run")
        }
    }

    return (
        <>
        <div className="h-full flex overflow-hidden">
            {/* Sidebar List */}
            <div className="w-80 border-r border-border bg-card flex flex-col">
                <div className="p-4 border-b border-border">
                    <h3 className="font-semibold text-foreground">History</h3>
                </div>
                <div className="flex-1 overflow-y-auto">
                    {runs.map(run => (
                        <div
                            key={run.id}
                            onClick={() => setSelectedRun(run.id)}
                            className={cn(
                                "p-4 border-b border-border cursor-pointer hover:bg-secondary/50 transition-colors group relative",
                                selectedRun === run.id ? "bg-secondary border-l-4 border-l-primary" : "border-l-4 border-l-transparent"
                            )}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-bold text-foreground text-sm">{run.id}</span>
                                <button
                                    onClick={(e) => deleteRun(run.id, e)}
                                    className="opacity-0 group-hover:opacity-100 text-muted-foreground hover:text-red-500 transition-opacity"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                            <div className="text-xs text-muted-foreground flex items-center gap-1 mb-2">
                                <Clock size={10} />
                                {new Date(run.timestamp).toLocaleString()}
                            </div>

                            {/* Tags */}
                            <div className="flex flex-wrap gap-2 mt-2">
                                {/* Problem Type Tag */}
                                {run.metrics?.problem_type && (
                                    <span className="text-[10px] bg-primary/10 text-primary px-1.5 py-0.5 rounded font-mono border border-primary/20">
                                        {run.metrics.problem_type}
                                    </span>
                                )}

                                {/* Mesh File Tag (Only if mesh problem) */}
                                {run.metrics?.mesh_file && run.metrics.problem_type && run.metrics.problem_type.includes('mesh') && (
                                    <span className="text-[10px] bg-secondary px-1.5 py-0.5 rounded text-muted-foreground font-mono border border-border">
                                        {run.metrics.mesh_file.split('/').pop()}
                                    </span>
                                )}

                                {/* MAE Tag (Only if valid) */}
                                {run.metrics && (run.metrics.pinn_mse || run.metrics.mae) && (
                                    <span className="text-[10px] bg-green-900/20 text-green-400 px-1.5 py-0.5 rounded font-mono border border-green-900/30">
                                        MAE: {run.metrics.mae ? run.metrics.mae.toExponential(1) : (run.metrics.pinn_mse ? run.metrics.pinn_mse.toExponential(1) : 'N/A')}
                                    </span>
                                )}
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col bg-background overflow-hidden">
                {selectedRun && runDetails ? (
                    <>
                        {/* Header */}
                        <div className="h-16 border-b border-border flex items-center justify-between px-6 bg-card">
                            <div className="flex items-center gap-4">
                                <h2 className="text-xl font-bold text-foreground">{selectedRun}</h2>
                                <div className="flex gap-2">
                                    <span className="px-2 py-1 bg-secondary rounded text-xs text-muted-foreground font-mono">
                                        {runDetails.config?.problem}
                                    </span>
                                    {runDetails.config?.problem?.includes('mesh') && (
                                        <span className="px-2 py-1 bg-secondary rounded text-xs text-muted-foreground font-mono">
                                            {runDetails.config?.mesh_file?.split('/').pop()}
                                        </span>
                                    )}
                                </div>
                            </div>
                            <div className="flex gap-2">
                                <a
                                    href={`http://localhost:8000/results/${selectedRun}/interactive_comparison_v2.html`}
                                    target="_blank"
                                    rel="noopener noreferrer"
                                    className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:opacity-90 transition-opacity text-sm font-medium"
                                >
                                    <Activity size={16} />
                                    Visualization
                                </a>
                                <button
                                    onClick={() => setShowDetails(true)}
                                    className="flex items-center gap-2 px-4 py-2 bg-secondary text-foreground rounded-lg hover:bg-secondary/80 transition-colors text-sm font-medium"
                                >
                                    <FileText size={16} />
                                    Details
                                </button>
                            </div>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-hidden relative">
                            <iframe
                                src={`http://localhost:8000/results/${selectedRun}/interactive_comparison_v2.html`}
                                className="w-full h-full border-0 bg-[#1e1e1e]"
                                title="Visualization"
                            />
                        </div>
                    </>
                ) : (
                    <div className="flex-1 flex items-center justify-center text-muted-foreground">
                        Select a run to view details
                    </div>
                )}
            </div>
        </div>
        {showDetails && selectedRun && runDetails && (
            <div className="fixed inset-0 z-50 flex justify-end bg-black/50 backdrop-blur-sm">
                <div className="h-full w-full max-w-2xl overflow-y-auto border-l border-border bg-card shadow-2xl">
                    <div className="sticky top-0 z-10 flex items-center justify-between border-b border-border bg-card/95 px-6 py-4 backdrop-blur">
                        <div>
                            <h3 className="text-lg font-bold text-foreground">Run Details</h3>
                            <p className="text-sm text-muted-foreground">{selectedRun}</p>
                        </div>
                        <button
                            onClick={() => setShowDetails(false)}
                            className="rounded-md border border-border px-3 py-1.5 text-sm text-muted-foreground hover:bg-secondary hover:text-foreground"
                        >
                            Close
                        </button>
                    </div>

                    <div className="space-y-6 p-6">
                        <section>
                            <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-primary">Config</h4>
                            {renderKeyValueList(runDetails.config)}
                        </section>

                        <section>
                            <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-primary">Metrics</h4>
                            {renderKeyValueList(runDetails.metrics)}
                        </section>

                        <section>
                            <h4 className="mb-3 text-sm font-semibold uppercase tracking-wide text-primary">Model Summary</h4>
                            {renderKeyValueList(runDetails.model_summary)}
                        </section>
                    </div>
                </div>
            </div>
        )}
        </>
    )
}
