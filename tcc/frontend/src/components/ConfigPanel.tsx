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
                                <option value="magnetostatic_mesh">Magnetostatic (Mesh)</option>
                                <option value="magnetodynamic_mesh">Magnetodynamic (Mesh)</option>
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

                {/* Problem Specific Parameters */}
                {config.problem === 'poisson_2d' && (
                    <Section title="Poisson 2D Parameters">
                        <div className="grid grid-cols-2 gap-6">
                            <InputGroup label="Lx (Width)">
                                <input
                                    type="number"
                                    step="0.1"
                                    value={config.Lx || 1.0}
                                    onChange={(e) => handleChange('Lx', parseFloat(e.target.value))}
                                    className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                />
                            </InputGroup>
                            <InputGroup label="Ly (Height)">
                                <input
                                    type="number"
                                    step="0.1"
                                    value={config.Ly || 1.0}
                                    onChange={(e) => handleChange('Ly', parseFloat(e.target.value))}
                                    className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                />
                            </InputGroup>
                        </div>
                    </Section>
                )}

                {config.problem === 'magnetodynamic_mesh' && (
                    <Section title="Magnetodynamic Parameters">
                        <div className="grid grid-cols-3 gap-6">
                            <InputGroup label="Frequency (Hz)">
                                <input
                                    type="number"
                                    step="10"
                                    value={config.frequency || 60}
                                    onChange={(e) => handleChange('frequency', parseFloat(e.target.value))}
                                    className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                />
                            </InputGroup>
                            <InputGroup label="Sigma (Conductivity)">
                                <input
                                    type="number"
                                    step="1000"
                                    value={config.sigma || 58000000}
                                    onChange={(e) => handleChange('sigma', parseFloat(e.target.value))}
                                    className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                />
                            </InputGroup>
                            <InputGroup label="Mu (Permeability)">
                                <input
                                    type="number"
                                    step="0.0001"
                                    value={config.mu || 1.0}
                                    onChange={(e) => handleChange('mu', parseFloat(e.target.value))}
                                    className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                />
                            </InputGroup>
                        </div>
                    </Section>
                )}

                {/* Slice Configuration (For Mesh Problems) */}
                {config.problem.includes('mesh') && config.slice_config && (
                    <Section title="Visualization Slice (1D)">
                        <div className="grid grid-cols-2 gap-6">
                            <InputGroup label="Start Point [x, y]">
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={config.slice_config.p_start[0]}
                                        onChange={(e) => {
                                            const newSlice = { ...config.slice_config }
                                            newSlice.p_start[0] = parseFloat(e.target.value)
                                            handleChange('slice_config', newSlice)
                                        }}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                        placeholder="X"
                                    />
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={config.slice_config.p_start[1]}
                                        onChange={(e) => {
                                            const newSlice = { ...config.slice_config }
                                            newSlice.p_start[1] = parseFloat(e.target.value)
                                            handleChange('slice_config', newSlice)
                                        }}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                        placeholder="Y"
                                    />
                                </div>
                            </InputGroup>
                            <InputGroup label="End Point [x, y]">
                                <div className="flex gap-2">
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={config.slice_config.p_end[0]}
                                        onChange={(e) => {
                                            const newSlice = { ...config.slice_config }
                                            newSlice.p_end[0] = parseFloat(e.target.value)
                                            handleChange('slice_config', newSlice)
                                        }}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                        placeholder="X"
                                    />
                                    <input
                                        type="number"
                                        step="0.1"
                                        value={config.slice_config.p_end[1]}
                                        onChange={(e) => {
                                            const newSlice = { ...config.slice_config }
                                            newSlice.p_end[1] = parseFloat(e.target.value)
                                            handleChange('slice_config', newSlice)
                                        }}
                                        className="w-full bg-secondary border border-input rounded-lg p-2 text-foreground"
                                        placeholder="Y"
                                    />
                                </div>
                            </InputGroup>
                        </div>
                    </Section>
                )}

                {/* Boundary Conditions */}
                <Section title="Boundary Conditions">
                    <div className="space-y-4">
                        {Object.entries(config.boundary_conditions || {}).map(([key, val]: any) => (
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
