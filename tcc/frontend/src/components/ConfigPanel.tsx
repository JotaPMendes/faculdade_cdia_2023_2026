import { useEffect, useState } from 'react'
import axios from 'axios'
import { Save, RefreshCw } from 'lucide-react'

export default function ConfigPanel() {
    const [config, setConfig] = useState<any>(null)
    const [loading, setLoading] = useState(true)
    const [saving, setSaving] = useState(false)

    useEffect(() => {
        fetchConfig()
    }, [])

    const fetchConfig = async () => {
        setLoading(true)
        try {
            const res = await axios.get('http://localhost:8000/config')
            setConfig(res.data)
        } catch (error) {
            console.error("Failed to fetch config", error)
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        setSaving(true)
        try {
            await axios.post('http://localhost:8000/config', config)
            alert("Configuration saved!")
        } catch (error) {
            console.error("Failed to save config", error)
            alert("Failed to save config")
        } finally {
            setSaving(false)
        }
    }

    const handleChange = (key: string, value: any) => {
        setConfig((prev: any) => ({ ...prev, [key]: value }))
    }

    if (loading) return <div className="p-8 text-foreground">Loading config...</div>

    return (
        <div className="p-8 max-w-4xl mx-auto space-y-8">
            <div className="flex items-center justify-between">
                <h2 className="text-3xl font-bold text-foreground">Configuration</h2>
                <div className="flex gap-3">
                    <button
                        onClick={fetchConfig}
                        className="p-2 bg-white/5 hover:bg-white/10 rounded-lg transition-colors"
                    >
                        <RefreshCw size={20} />
                    </button>
                    <button
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center gap-2 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors disabled:opacity-50"
                    >
                        <Save size={18} />
                        {saving ? "Saving..." : "Save Changes"}
                    </button>
                </div>
            </div>

            <div className="space-y-6">
                {/* General Settings */}
                <Section title="General Settings">
                    <div className="grid grid-cols-2 gap-6">
                        <InputGroup label="Problem Type">
                            <select
                                value={config.problem}
                                onChange={(e) => handleChange('problem', e.target.value)}
                                className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                            >
                                <option value="electrostatic_mesh">Electrostatic (Mesh)</option>
                                <option value="poisson_2d">Poisson 2D</option>
                                <option value="heat_1d">Heat 1D</option>
                                <option value="wave_1d">Wave 1D</option>
                            </select>
                        </InputGroup>

                        <InputGroup label="Mesh File">
                            <input
                                type="text"
                                value={config.mesh_file}
                                onChange={(e) => handleChange('mesh_file', e.target.value)}
                                className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                            />
                        </InputGroup>
                    </div>
                </Section>

                {/* Training Parameters */}
                <Section title="Training Parameters">
                    <div className="grid grid-cols-2 gap-6">
                        <InputGroup label="Training Points (N_data)">
                            <input
                                type="number"
                                value={config.N_data}
                                onChange={(e) => handleChange('N_data', parseInt(e.target.value))}
                                className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                            />
                        </InputGroup>

                        <InputGroup label="Test Points (N_test)">
                            <input
                                type="number"
                                value={config.N_test}
                                onChange={(e) => handleChange('N_test', parseInt(e.target.value))}
                                className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                            />
                        </InputGroup>
                    </div>
                </Section>

                {/* Boundary Conditions */}
                <Section title="Boundary Conditions">
                    <div className="space-y-4">
                        {Object.entries(config.boundary_conditions).map(([key, val]: any) => (
                            <div key={key} className="flex items-center gap-4">
                                <label className="w-32 text-sm text-muted-foreground">{key}</label>
                                <input
                                    type="number"
                                    step="0.1"
                                    value={val}
                                    onChange={(e) => {
                                        const newBCs = { ...config.boundary_conditions, [key]: parseFloat(e.target.value) }
                                        handleChange('boundary_conditions', newBCs)
                                    }}
                                    className="flex-1 bg-secondary border border-input rounded-lg p-2 text-foreground"
                                />
                            </div>
                        ))}
                    </div>
                </Section>
            </div>
        </div>
    )
}

function Section({ title, children }: any) {
    return (
        <div className="p-6 rounded-xl bg-card border border-white/10">
            <h3 className="text-lg font-semibold mb-4 text-foreground">{title}</h3>
            {children}
        </div>
    )
}

function InputGroup({ label, children }: any) {
    return (
        <div className="space-y-2">
            <label className="text-sm font-medium text-muted-foreground">{label}</label>
            {children}
        </div>
    )
}
