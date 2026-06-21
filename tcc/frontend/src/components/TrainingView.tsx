import { useState, useEffect, useRef } from 'react'
import axios from 'axios'
import { Play, Square, Terminal, TrendingDown } from 'lucide-react'
import { cn } from '../utils/cn'
import {
    LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer
} from 'recharts'

interface MetricPoint {
    step: number
    trainLoss: number
}

const MAX_CHART_POINTS = 400

function parseMetricFromLog(line: string): MetricPoint | null {
    // DeepXDE format: "  1000 [5.92e-02, 4.77e-04, ...] [...]"
    const match = line.match(/^\s*(\d+)\s+\[([\d\s.,e+\-]+)\]/)
    if (!match) return null
    const step = parseInt(match[1], 10)
    const losses = match[2]
        .split(',')
        .map(s => parseFloat(s.trim()))
        .filter(v => isFinite(v) && v > 0)
    if (losses.length === 0) return null
    const trainLoss = losses.reduce((a, b) => a + b, 0)
    return { step, trainLoss }
}

export default function TrainingView() {
    const [config, setConfig] = useState<any>(null)
    const [meshes, setMeshes] = useState<string[]>([])
    const [meshBoundaries, setMeshBoundaries] = useState<string[]>([])
    const [training, setTraining] = useState(false)
    const [logs, setLogs] = useState<string[]>([])
    const [runId, setRunId] = useState<string | null>(null)
    const [metrics, setMetrics] = useState<MetricPoint[]>([])
    const logsEndRef = useRef<HTMLDivElement>(null)

    useEffect(() => {
        fetchConfig()
        fetchMeshes()
    }, [])

    useEffect(() => {
        if (config?.mesh_file) {
            const filename = config.mesh_file.split('/').pop()
            fetchMeshBoundaries(filename)
        }
    }, [config?.mesh_file])

    useEffect(() => {
        if (logsEndRef.current) {
            logsEndRef.current.scrollIntoView({ behavior: 'smooth' })
        }
    }, [logs])

    const fetchConfig = async () => {
        const res = await axios.get('http://localhost:8000/config')
        setConfig(res.data)
    }

    const fetchMeshes = async () => {
        const res = await axios.get('http://localhost:8000/meshes')
        setMeshes(res.data)
    }

    const fetchMeshBoundaries = async (filename: string) => {
        try {
            const res = await axios.get(`http://localhost:8000/meshes/${filename}/boundaries`)
            const boundaries: string[] = res.data
            setMeshBoundaries(boundaries)
            // rebuild boundary_conditions keeping existing values, dropping removed, adding new
            setConfig((prev: any) => {
                const existing = prev.boundary_conditions || {}
                const updated: Record<string, number> = {}
                for (const b of boundaries) {
                    updated[b] = existing[b] ?? 0.0
                }
                return { ...prev, boundary_conditions: updated }
            })
        } catch {
            setMeshBoundaries([])
        }
    }

    const startTraining = async () => {
        try {
            // Primeiro salvar config
            await axios.post('http://localhost:8000/config', config)

            // Iniciar treino
            const res = await axios.post('http://localhost:8000/train')
            setRunId(res.data.run_id)
            setTraining(true)
            setMetrics([])
            setLogs(prev => [...prev, "--- UI: Training Started ---"])

            // Conectar WebSocket
            const ws = new WebSocket('ws://localhost:8000/ws/logs')

            ws.onopen = () => {
                setLogs(prev => [...prev, "--- UI: WS Connected ---"])
            }

            ws.onmessage = (event) => {
                const point = parseMetricFromLog(event.data)
                if (point) {
                    setMetrics(prev => {
                        const next = [...prev, point]
                        return next.length > MAX_CHART_POINTS
                            ? next.slice(next.length - MAX_CHART_POINTS)
                            : next
                    })
                }
                setLogs(prev => [...prev, event.data])
            }

            ws.onerror = (e) => {
                setLogs(prev => [...prev, "--- UI: WS Error ---"])
                console.error(e)
            }

            ws.onclose = (e) => {
                setLogs(prev => [...prev, `--- UI: WS Closed (Code: ${e.code}) ---`])
                setTraining(false)
            }
        } catch (error: any) {
            alert(`Error starting training: ${error.message}`)
            setLogs(prev => [...prev, `--- UI: Error: ${error.message} ---`])
            setTraining(false)
        }
    }

    const stopTraining = async () => {
        try {
            await axios.post('http://localhost:8000/stop')
            setTraining(false)
        } catch (error) {
            console.error(error)
        }
    }

    const clearLogs = () => {
        setLogs([])
        setMetrics([])
    }

    const handleFileUpload = async (event: any) => {
        const file = event.target.files[0]
        if (!file) return

        const formData = new FormData()
        formData.append('file', file)

        try {
            await axios.post('http://localhost:8000/mesh/upload', formData, {
                headers: { 'Content-Type': 'multipart/form-data' }
            })
            alert(`Mesh ${file.name} uploaded successfully!`)
            fetchMeshes()
            // Auto-select the uploaded mesh
            setConfig((prev: any) => ({ ...prev, mesh_file: `meshes/files/${file.name}` }))
        } catch (error) {
            alert("Failed to upload mesh")
        }
    }

    if (!config) return <div>Loading...</div>

    return (
        <div className="p-8 h-full flex flex-col">
            <h2 className="text-3xl font-bold text-foreground mb-6">Training Center</h2>

            <div className="grid grid-cols-3 gap-8 flex-1 min-h-0">
                {/* Config Column */}
                <div className="col-span-1 space-y-6 overflow-auto pr-4">
                    <div className="bg-card border border-border rounded-xl p-6 space-y-6">
                        <h3 className="text-lg font-semibold text-foreground border-b border-border pb-2">Setup</h3>

                        <div className="space-y-4">
                            <div>
                                <label className="text-sm text-muted-foreground font-medium">Problem Type</label>
                                <select
                                    value={config.problem}
                                    onChange={e => setConfig({ ...config, problem: e.target.value })}
                                    className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                >
                                    <option value="electrostatic_mesh">Electrostatic (Mesh)</option>
                                    <option value="poisson_2d">Poisson 2D</option>
                                    <option value="heat_1d">Heat 1D</option>
                                    <option value="wave_1d">Wave 1D</option>
                                </select>
                            </div>

                            <div className="grid grid-cols-2 gap-4">
                                <div>
                                    <label className="text-sm text-muted-foreground font-medium">N_data</label>
                                    <input
                                        type="number"
                                        value={config.N_data}
                                        onChange={e => setConfig({ ...config, N_data: parseInt(e.target.value) })}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                    />
                                </div>
                                <div>
                                    <label className="text-sm text-muted-foreground font-medium">N_test</label>
                                    <input
                                        type="number"
                                        value={config.N_test}
                                        onChange={e => setConfig({ ...config, N_test: parseInt(e.target.value) })}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Dynamic Fields based on Problem */}
                        {/* Mesh Problems (Electrostatic, Magnetostatic, Magnetodynamic) */}
                        {config.problem.includes('mesh') && (
                            <div className="space-y-6 pt-4 border-t border-border">
                                <h4 className="font-semibold text-foreground">Mesh Settings</h4>

                                {/* Mesh Selection & Upload */}
                                <div className="space-y-3">
                                    <label className="text-sm text-muted-foreground font-medium">Mesh Selection</label>
                                    <select
                                        value={config.mesh_file.split('/').pop()}
                                        onChange={e => {
                                            setConfig({ ...config, mesh_file: `meshes/files/${e.target.value}` })
                                            fetchMeshBoundaries(e.target.value)
                                        }}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                    >
                                        {meshes.map(m => <option key={m} value={m}>{m}</option>)}
                                    </select>

                                    <div className="pt-2">
                                        <label className="text-xs text-muted-foreground font-medium mb-1 block">Upload .msh file</label>
                                        <input
                                            type="file"
                                            accept=".msh"
                                            onChange={handleFileUpload}
                                            className="w-full text-xs text-muted-foreground file:mr-2 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-xs file:font-semibold file:bg-primary file:text-primary-foreground hover:file:bg-primary/90"
                                        />
                                    </div>
                                </div>

                                {/* Boundary Conditions */}
                                <div>
                                    <label className="text-sm text-muted-foreground font-medium mb-2 block">Boundary Conditions</label>
                                    <div className="grid grid-cols-2 gap-x-4 gap-y-2">
                                        {Object.entries(config.boundary_conditions || {}).map(([key, val]: any) => (
                                            <div key={key} className="flex items-center justify-between bg-secondary/50 p-2 rounded border border-border">
                                                <span className="text-xs text-muted-foreground font-mono">{key}</span>
                                                <input
                                                    type="number"
                                                    value={val}
                                                    onChange={e => {
                                                        const newBC = { ...config.boundary_conditions, [key]: parseFloat(e.target.value) }
                                                        setConfig({ ...config, boundary_conditions: newBC })
                                                    }}
                                                    className="w-16 bg-background border border-input rounded px-1 text-sm text-right"
                                                />
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Poisson 2D Settings */}
                        {config.problem === 'poisson_2d' && (
                            <div className="space-y-4 pt-4 border-t border-border">
                                <h4 className="font-semibold text-foreground">Poisson Settings</h4>
                                <div className="grid grid-cols-2 gap-4">
                                    <div>
                                        <label className="text-sm text-muted-foreground font-medium">Lx (Width)</label>
                                        <input
                                            type="number"
                                            value={config.Lx || 1.0}
                                            onChange={e => setConfig({ ...config, Lx: parseFloat(e.target.value) })}
                                            className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm text-muted-foreground font-medium">Ly (Height)</label>
                                        <input
                                            type="number"
                                            value={config.Ly || 1.0}
                                            onChange={e => setConfig({ ...config, Ly: parseFloat(e.target.value) })}
                                            className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm text-muted-foreground font-medium">Nx (Train Grid)</label>
                                        <input
                                            type="number"
                                            value={config.Nx_train || 50}
                                            onChange={e => setConfig({ ...config, Nx_train: parseInt(e.target.value) })}
                                            className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm text-muted-foreground font-medium">Ny (Train Grid)</label>
                                        <input
                                            type="number"
                                            value={config.Ny_train || 50}
                                            onChange={e => setConfig({ ...config, Ny_train: parseInt(e.target.value) })}
                                            className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                        />
                                    </div>
                                </div>
                            </div>
                        )}

                        {/* Heat/Wave 1D Settings */}
                        {(config.problem === 'heat_1d' || config.problem === 'wave_1d') && (
                            <div className="space-y-4 pt-4 border-t border-border">
                                <h4 className="font-semibold text-foreground">1D Problem Settings</h4>
                                <div className="grid grid-cols-3 gap-4">
                                    <div>
                                        <label className="text-sm text-muted-foreground font-medium">Length (Lx)</label>
                                        <input
                                            type="number"
                                            value={config.Lx || 1.0}
                                            onChange={e => setConfig({ ...config, Lx: parseFloat(e.target.value) })}
                                            className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                        />
                                    </div>
                                    <div>
                                        <label className="text-sm text-muted-foreground font-medium">Time (T_train)</label>
                                        <input
                                            type="number"
                                            value={config.T_train || 1.0}
                                            onChange={e => setConfig({ ...config, T_train: parseFloat(e.target.value) })}
                                            className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                        />
                                    </div>
                                    {config.problem === 'heat_1d' && (
                                        <div>
                                            <label className="text-sm text-muted-foreground font-medium">Alpha</label>
                                            <input
                                                type="number"
                                                value={config.alpha || 0.01}
                                                onChange={e => setConfig({ ...config, alpha: parseFloat(e.target.value) })}
                                                className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                            />
                                        </div>
                                    )}
                                    {config.problem === 'wave_1d' && (
                                        <div>
                                            <label className="text-sm text-muted-foreground font-medium">Wave Speed (c)</label>
                                            <input
                                                type="number"
                                                value={config.c || 1.0}
                                                onChange={e => setConfig({ ...config, c: parseFloat(e.target.value) })}
                                                className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground mt-1"
                                            />
                                        </div>
                                    )}
                                </div>
                            </div>
                        )}
                    </div>

                    <button
                        onClick={training ? stopTraining : startTraining}
                        className={cn(
                            "w-full py-4 rounded-xl font-bold text-lg flex items-center justify-center gap-2 transition-all shadow-lg",
                            training
                                ? "bg-red-500 text-white hover:bg-red-600"
                                : "bg-primary text-primary-foreground hover:opacity-90"
                        )}
                    >
                        {training ? <><Square size={20} /> STOP TRAINING</> : <><Play size={20} /> START TRAINING</>}
                    </button>
                </div>

                {/* Right Panel: Chart + Logs */}
                <div className="col-span-2 flex flex-col gap-4 min-h-0">
                    {/* Loss Chart */}
                    <div className="bg-card border border-border rounded-xl p-4 flex flex-col flex-none" style={{ height: '220px' }}>
                        <div className="flex items-center gap-2 text-muted-foreground mb-2 border-b border-border pb-2">
                            <TrendingDown size={16} />
                            <span className="text-sm font-medium text-foreground">Loss Curve</span>
                            {metrics.length > 0 && (
                                <span className="ml-auto text-xs font-mono bg-secondary px-2 py-0.5 rounded text-muted-foreground">
                                    step {metrics[metrics.length - 1].step}
                                    &nbsp;·&nbsp;
                                    {metrics[metrics.length - 1].trainLoss.toExponential(3)}
                                </span>
                            )}
                        </div>
                        <div className="flex-1 min-h-0">
                            <LossChart data={metrics} />
                        </div>
                    </div>

                    {/* Logs */}
                    <div className="bg-black rounded-xl border border-border p-4 flex flex-col font-mono text-sm flex-1 min-h-0 shadow-inner">
                        <div className="flex items-center gap-2 text-muted-foreground mb-2 border-b border-white/10 pb-2">
                            <Terminal size={16} />
                            <span>Live Logs {runId && `(${runId})`}</span>
                        </div>
                        <div className="flex-1 overflow-y-auto space-y-1 p-2">
                            {logs.map((log, i) => (
                                <div key={i} className="text-gray-300 whitespace-pre-wrap font-mono text-xs">{log}</div>
                            ))}
                            <div ref={logsEndRef} />
                            {logs.length === 0 && <span className="text-muted-foreground italic">Ready to train...</span>}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    )
}

function LossChart({ data }: { data: MetricPoint[] }) {
    if (data.length === 0) {
        return (
            <div className="h-full flex items-center justify-center">
                <span className="text-muted-foreground text-sm italic">Loss curve will appear when training starts...</span>
            </div>
        )
    }

    return (
        <ResponsiveContainer width="100%" height="100%">
            <LineChart data={data} margin={{ top: 4, right: 16, left: 4, bottom: 4 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(128,128,128,0.12)" />
                <XAxis
                    dataKey="step"
                    tick={{ fontSize: 10, fill: '#888' }}
                    tickLine={false}
                    axisLine={{ stroke: '#333' }}
                    tickFormatter={(v: number) => v >= 1000 ? `${(v / 1000).toFixed(0)}k` : `${v}`}
                />
                <YAxis
                    scale="log"
                    domain={['auto', 'auto']}
                    allowDataOverflow
                    tick={{ fontSize: 10, fill: '#888' }}
                    tickLine={false}
                    axisLine={{ stroke: '#333' }}
                    tickFormatter={(v: number) => v.toExponential(0)}
                    width={52}
                />
                <Tooltip
                    contentStyle={{ background: '#111827', border: '1px solid #374151', borderRadius: 6, fontSize: 12 }}
                    labelStyle={{ color: '#9ca3af', marginBottom: 4 }}
                    labelFormatter={(v: number) => `Step ${v}`}
                    formatter={(v: number) => [v.toExponential(4), 'Train Loss']}
                    cursor={{ stroke: '#4b5563', strokeWidth: 1 }}
                />
                <Line
                    type="monotone"
                    dataKey="trainLoss"
                    stroke="#3b82f6"
                    strokeWidth={1.5}
                    dot={false}
                    isAnimationActive={false}
                />
            </LineChart>
        </ResponsiveContainer>
    )
}
