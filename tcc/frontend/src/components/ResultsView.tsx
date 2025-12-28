import { useState, useEffect } from 'react'
import axios from 'axios'
import { ChevronRight, BarChart2 } from 'lucide-react'

export default function ResultsView() {
    const [runs, setRuns] = useState<any[]>([])
    const [selectedRun, setSelectedRun] = useState<any>(null)

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
    }

    return (
        <div className="p-8 h-full flex gap-8">
            {/* Sidebar List */}
            <div className="w-1/3 flex flex-col gap-4">
                <h2 className="text-2xl font-bold text-foreground mb-4">Run History</h2>
                <div className="flex-1 overflow-auto space-y-3 pr-2">
                    {runs.map(run => (
                        <button
                            key={run.id}
                            onClick={() => fetchRunDetails(run.id)}
                            className={`w-full text-left p-4 rounded-xl border transition-all ${selectedRun?.id === run.id
                                ? "bg-primary/20 border-primary text-foreground"
                                : "bg-card border-white/10 text-muted-foreground hover:bg-white/5"
                                }`}
                        >
                            <div className="flex justify-between items-center mb-2">
                                <span className="font-mono text-xs opacity-70">{new Date(run.timestamp).toLocaleString()}</span>
                                {selectedRun?.id === run.id && <ChevronRight size={16} />}
                            </div>
                            <div className="font-bold truncate">{run.id}</div>
                            <div className="text-xs mt-2 flex gap-2">
                                <span className="bg-white/10 px-2 py-1 rounded">PINN: {run.metrics?.PINN?.toExponential(2) || "N/A"}</span>
                            </div>
                        </button>
                    ))}
                </div>
            </div>

            {/* Details Panel */}
            <div className="flex-1 bg-card border border-white/10 rounded-xl p-8 overflow-auto">
                {selectedRun ? (
                    <div className="space-y-8">
                        <div className="flex justify-between items-start">
                            <div>
                                <h2 className="text-3xl font-bold text-foreground">{selectedRun.id}</h2>
                                <p className="text-muted-foreground mt-1">
                                    Problem: {selectedRun.config?.problem} • Mesh: {selectedRun.config?.mesh_file}
                                </p>
                            </div>
                            <div className="text-right">
                                <div className="text-sm text-muted-foreground">PINN MAE</div>
                                <div className="text-3xl font-bold text-cyan-400">
                                    {selectedRun.metrics?.PINN?.toExponential(2)}
                                </div>
                            </div>
                        </div>

                        <div className="grid grid-cols-2 gap-6">
                            <div className="bg-black/20 p-4 rounded-lg">
                                <h3 className="text-sm font-bold text-foreground mb-3 flex items-center gap-2">
                                    <BarChart2 size={16} /> Model Architecture
                                </h3>
                                <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap">
                                    {JSON.stringify(selectedRun.model_summary, null, 2)}
                                </pre>
                            </div>
                            <div className="bg-black/20 p-4 rounded-lg">
                                <h3 className="text-sm font-bold text-foreground mb-3">Configuration</h3>
                                <pre className="text-xs text-muted-foreground font-mono whitespace-pre-wrap">
                                    {JSON.stringify(selectedRun.config, null, 2)}
                                </pre>
                            </div>
                        </div>

                        {/* Plots */}
                        <div className="h-[600px] bg-black/20 rounded-lg overflow-hidden border border-white/10">
                            <iframe
                                src={`http://localhost:8000/results/${selectedRun.id}/interactive_comparison_v2.html`}
                                className="w-full h-full border-none bg-background"
                                title="Comparison Plot"
                            />
                        </div>
                    </div>
                ) : (
                    <div className="h-full flex items-center justify-center text-muted-foreground">
                        Select a run to view details
                    </div>
                )}
            </div>
        </div>
    )
}
