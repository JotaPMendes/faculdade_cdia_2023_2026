import { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronRight, BarChart2, Settings, Activity, Layers, Trash2 } from 'lucide-react'
import { cn } from '../utils/cn'

export default function ResultsView() {
    const [runs, setRuns] = useState<any[]>([])
    const [selectedRun, setSelectedRun] = useState<any>(null)
    const [activeTab, setActiveTab] = useState<'viz' | 'details'>('viz')

    useEffect(() => {
        fetchRuns()
    }, [])

    const fetchRuns = async () => {
        const res = await axios.get('http://localhost:8000/runs')
        setRuns(res.data)
    }

    const fetchRunDetails = async (runId: string) => {
        const res = await axios.get(`http://localhost:8000/runs/${runId}`)
        setSelectedRun(res.data)
        setActiveTab('viz') // Reset to visualization when switching runs
    }

    const deleteRun = async (e: React.MouseEvent, runId: string) => {
        e.stopPropagation() // Prevent selecting the run when clicking delete
        if (!confirm(`Are you sure you want to delete run ${runId}?`)) return

        try {
            await axios.delete(`http://localhost:8000/runs/${runId}`)
            if (selectedRun?.id === runId) {
                setSelectedRun(null)
            }
            fetchRuns()
        } catch (error) {
            alert("Failed to delete run")
        }
    }

    return (
        <div className="flex h-full bg-background">
            {/* Sidebar List */}
            <div className="w-72 border-r border-border flex flex-col bg-card">
                <div className="p-4 border-b border-border">
                    <h2 className="text-xl font-bold text-foreground flex items-center gap-2">
                        <Activity size={20} className="text-primary" />
                        Run History
                    </h2>
                </div>
                <div className="flex-1 overflow-auto p-2 space-y-2">
                    {runs.map(run => (
                        <button
                            key={run.id}
                            onClick={() => fetchRunDetails(run.id)}
                            className={cn(
                                "w-full text-left p-3 rounded-lg border transition-all group",
                                selectedRun?.id === run.id
                                    ? "bg-primary/10 border-primary/50 text-foreground shadow-sm"
                                    : "bg-transparent border-transparent text-muted-foreground hover:bg-secondary hover:text-foreground"
                            )}
                        >
                            <div className="flex justify-between items-center mb-1">
                                <span className="font-mono text-[10px] opacity-70 uppercase tracking-wider">
                                    {new Date(run.timestamp).toLocaleDateString()} {new Date(run.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                </span>
                                {selectedRun?.id === run.id && <ChevronRight size={14} className="text-primary" />}
                            </div>
                            <div className="font-medium text-sm truncate mb-1">{run.id}</div>
                            <div className="flex items-center justify-between">
                                <span className={cn(
                                    "text-[10px] px-1.5 py-0.5 rounded border",
                                    run.metrics?.PINN < 1e-3
                                        ? "bg-green-500/10 text-green-500 border-green-500/20"
                                        : "bg-secondary text-muted-foreground border-border"
                                )}>
                                    MAE: {run.metrics?.PINN?.toExponential(1) || "N/A"}
                                </span>
                                <button
                                    onClick={(e) => deleteRun(e, run.id)}
                                    className="p-1 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded transition-colors opacity-0 group-hover:opacity-100"
                                    title="Delete Run"
                                >
                                    <Trash2 size={14} />
                                </button>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Main Content */}
            <div className="flex-1 flex flex-col min-w-0 bg-background">
                {selectedRun ? (
                    <>
                        {/* Header */}
                        <div className="h-16 border-b border-border flex items-center justify-between px-6 bg-card/50 backdrop-blur-sm">
                            <div className="flex items-center gap-4">
                                <h2 className="text-lg font-bold text-foreground">{selectedRun.id}</h2>
                                <div className="h-4 w-px bg-border" />
                                <div className="flex items-center gap-2 text-sm text-muted-foreground">
                                    <span className="px-2 py-0.5 rounded-full bg-secondary text-xs font-medium border border-border">
                                        {selectedRun.config?.problem}
                                    </span>
                                    {selectedRun.config?.mesh_file && (
                                        <span className="text-xs truncate max-w-[200px]" title={selectedRun.config.mesh_file}>
                                            {selectedRun.config.mesh_file.split('/').pop()}
                                        </span>
                                    )}
                                </div>
                            </div>

                            {/* Tabs */}
                            <div className="flex bg-secondary/50 p-1 rounded-lg border border-border">
                                <button
                                    onClick={() => setActiveTab('viz')}
                                    className={cn(
                                        "px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                                        activeTab === 'viz'
                                            ? "bg-background text-foreground shadow-sm"
                                            : "text-muted-foreground hover:text-foreground"
                                    )}
                                >
                                    <BarChart2 size={14} />
                                    Visualization
                                </button>
                                <button
                                    onClick={() => setActiveTab('details')}
                                    className={cn(
                                        "px-3 py-1.5 rounded-md text-sm font-medium transition-all flex items-center gap-2",
                                        activeTab === 'details'
                                            ? "bg-background text-foreground shadow-sm"
                                            : "text-muted-foreground hover:text-foreground"
                                    )}
                                >
                                    <Layers size={14} />
                                    Details
                                </button>
                            </div>
                        </div>

                        {/* Content Area */}
                        <div className="flex-1 overflow-hidden relative">
                            {activeTab === 'viz' && (
                                <div className="absolute inset-0 p-4">
                                    <div className="w-full h-full bg-card rounded-xl border border-border overflow-hidden shadow-sm relative group">
                                        <iframe
                                            src={`http://localhost:8000/results/${selectedRun.id}/interactive_comparison_v2.html`}
                                            className="w-full h-full border-none bg-white"
                                            title="Comparison Plot"
                                        />
                                        {/* Overlay hint */}
                                        <div className="absolute top-4 right-4 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity">
                                            <span className="bg-black/75 text-white text-xs px-2 py-1 rounded backdrop-blur-sm">
                                                Interactive Plotly View
                                            </span>
                                        </div>
                                    </div>
                                </div>
                            )}

                            {activeTab === 'details' && (
                                <div className="h-full overflow-auto p-6">
                                    <div className="max-w-4xl mx-auto grid grid-cols-2 gap-6">
                                        {/* Metrics Card */}
                                        <div className="col-span-2 bg-card border border-border rounded-xl p-6">
                                            <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                                                <Activity size={16} className="text-primary" />
                                                Performance Metrics
                                            </h3>
                                            <div className="grid grid-cols-4 gap-4">
                                                <div className="p-4 bg-secondary/30 rounded-lg border border-border">
                                                    <div className="text-xs text-muted-foreground mb-1">PINN MAE</div>
                                                    <div className="text-xl font-mono font-bold text-foreground">
                                                        {selectedRun.metrics?.PINN?.toExponential(2)}
                                                    </div>
                                                </div>
                                                <div className="p-4 bg-secondary/30 rounded-lg border border-border">
                                                    <div className="text-xs text-muted-foreground mb-1">Training Time</div>
                                                    <div className="text-xl font-mono font-bold text-foreground">
                                                        {selectedRun.metrics?.training_time ? `${selectedRun.metrics.training_time.toFixed(1)}s` : "N/A"}
                                                    </div>
                                                </div>
                                                <div className="p-4 bg-secondary/30 rounded-lg border border-border">
                                                    <div className="text-xs text-muted-foreground mb-1">Steps</div>
                                                    <div className="text-xl font-mono font-bold text-foreground">
                                                        {selectedRun.config?.pinn_config?.train_steps_adam + selectedRun.config?.pinn_config?.train_steps_lbfgs || "N/A"}
                                                    </div>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Architecture */}
                                        <div className="bg-card border border-border rounded-xl p-6">
                                            <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                                                <Layers size={16} className="text-primary" />
                                                Model Architecture
                                            </h3>
                                            <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap bg-secondary/30 p-4 rounded-lg border border-border overflow-auto max-h-[400px]">
                                                {JSON.stringify(selectedRun.model_summary, null, 2)}
                                            </pre>
                                        </div>

                                        {/* Configuration */}
                                        <div className="bg-card border border-border rounded-xl p-6">
                                            <h3 className="text-sm font-semibold text-foreground mb-4 flex items-center gap-2">
                                                <Settings size={16} className="text-primary" />
                                                Full Configuration
                                            </h3>
                                            <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap bg-secondary/30 p-4 rounded-lg border border-border overflow-auto max-h-[400px]">
                                                {JSON.stringify(selectedRun.config, null, 2)}
                                            </pre>
                                        </div>
                                    </div>
                                </div>
                            )}
                        </div>
                    </>
                ) : (
                    <div className="h-full flex flex-col items-center justify-center text-muted-foreground gap-4">
                        <div className="w-16 h-16 rounded-full bg-secondary flex items-center justify-center">
                            <BarChart2 size={32} className="opacity-50" />
                        </div>
                        <p>Select a run from the history to view results</p>
                    </div>
                )}
            </div>
        </div>
    )
}
