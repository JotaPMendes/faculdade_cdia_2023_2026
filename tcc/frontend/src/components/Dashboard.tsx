import { useEffect, useState } from 'react'
import axios from 'axios'
import { Activity, Zap, Clock } from 'lucide-react'
import { cn } from '../utils/cn'

export default function Dashboard() {
    const [metrics, setMetrics] = useState<any>(null)
    const [loading, setLoading] = useState(true)

    useEffect(() => {
        fetchMetrics()
    }, [])

    const fetchMetrics = async () => {
        try {
            const res = await axios.get('http://localhost:8000/metrics')
            setMetrics(res.data)
        } catch (error) {
            console.error("Failed to fetch metrics", error)
        } finally {
            setLoading(false)
        }
    }

    if (loading) return <div className="p-8 text-foreground">Loading metrics...</div>

    return (
        <div className="p-8 space-y-8">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-foreground">Dashboard</h2>
                <button
                    onClick={fetchMetrics}
                    className="px-4 py-2 bg-white/5 hover:bg-white/10 text-sm rounded-lg transition-colors"
                >
                    Refresh
                </button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <MetricCard
                    title="PINN MAE"
                    value={metrics?.PINN ? metrics.PINN.toExponential(2) : "N/A"}
                    icon={Zap}
                    color="text-cyan-400"
                />
                <MetricCard
                    title="FEM MAE"
                    value={metrics?.FEM ? metrics.FEM.toExponential(2) : "N/A"}
                    icon={Activity}
                    color="text-orange-400"
                />
                <MetricCard
                    title="Best ML Model"
                    value={metrics ? getBestML(metrics) : "N/A"}
                    icon={Clock}
                    color="text-green-400"
                />
            </div>

            {/* Placeholder for Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <div className="h-64 bg-card border border-white/10 rounded-xl p-6 flex items-center justify-center text-muted-foreground">
                    Loss History Chart (Coming Soon)
                </div>
                <div className="h-64 bg-card border border-white/10 rounded-xl p-6 flex items-center justify-center text-muted-foreground">
                    Prediction vs Truth (Coming Soon)
                </div>
            </div>
        </div>
    )
}

function MetricCard({ title, value, icon: Icon, color }: any) {
    return (
        <div className="p-6 rounded-xl bg-card border border-white/10 hover:border-white/20 transition-all group">
            <div className="flex justify-between items-start">
                <div>
                    <p className="text-sm text-muted-foreground font-medium">{title}</p>
                    <h3 className="text-3xl font-bold text-foreground mt-2">{value}</h3>
                </div>
                <div className={cn("p-3 rounded-lg bg-white/5 group-hover:bg-white/10 transition-colors", color)}>
                    <Icon size={24} />
                </div>
            </div>
        </div>
    )
}

function getBestML(metrics: any) {
    const ignore = ["PINN", "FEM"]
    const ml_keys = Object.keys(metrics).filter(k => !ignore.includes(k))
    if (ml_keys.length === 0) return "N/A"

    const best = ml_keys.reduce((a, b) => metrics[a] < metrics[b] ? a : b)
    return `${best} (${metrics[best].toExponential(2)})`
}
