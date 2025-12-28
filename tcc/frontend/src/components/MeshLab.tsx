import { useState, useEffect } from 'react'
import axios from 'axios'
import { Box, Plus, RefreshCw } from 'lucide-react'

export default function MeshLab() {
    const [meshes, setMeshes] = useState<string[]>([])
    const [generating, setGenerating] = useState(false)

    useEffect(() => {
        fetchMeshes()
    }, [])

    const fetchMeshes = async () => {
        const res = await axios.get('http://localhost:8000/meshes')
        setMeshes(res.data)
    }

    const generateMesh = async (type: string) => {
        setGenerating(true)
        try {
            await axios.post('http://localhost:8000/mesh/generate', { type })
            alert("Mesh generated successfully!")
            fetchMeshes()
        } catch (error) {
            alert("Failed to generate mesh")
        } finally {
            setGenerating(false)
        }
    }

    return (
        <div className="p-8">
            <div className="flex justify-between items-center mb-8">
                <h2 className="text-3xl font-bold text-foreground">Mesh Lab</h2>
                <button onClick={fetchMeshes} className="p-2 hover:bg-white/10 rounded-lg"><RefreshCw size={20} /></button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
                {/* Available Meshes */}
                <div className="bg-card border border-white/10 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                        <Box size={20} /> Available Meshes
                    </h3>
                    <div className="space-y-2">
                        {meshes.map(mesh => (
                            <div key={mesh} className="p-3 bg-black/20 rounded-lg flex justify-between items-center">
                                <span className="font-mono text-sm">{mesh}</span>
                                <span className="text-xs text-muted-foreground">Ready</span>
                            </div>
                        ))}
                        {meshes.length === 0 && <p className="text-muted-foreground">No meshes found.</p>}
                    </div>
                </div>

                {/* Generator */}
                <div className="bg-card border border-white/10 rounded-xl p-6">
                    <h3 className="text-xl font-bold text-foreground mb-4 flex items-center gap-2">
                        <Plus size={20} /> Generate New
                    </h3>
                    <div className="grid grid-cols-1 gap-4">
                        <GeneratorButton
                            label="Motor Stator"
                            desc="Complex geometry with internal slots"
                            onClick={() => generateMesh('stator')}
                            disabled={generating}
                        />
                        <GeneratorButton
                            label="Plate with Holes"
                            desc="Square plate with random circular holes"
                            onClick={() => generateMesh('plate')}
                            disabled={generating}
                        />
                        <GeneratorButton
                            label="L-Shape"
                            desc="Simple L-shaped domain with corner singularity"
                            onClick={() => generateMesh('lshape')}
                            disabled={generating}
                        />
                    </div>
                </div>
            </div>
        </div>
    )
}

function GeneratorButton({ label, desc, onClick, disabled }: any) {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className="text-left p-4 rounded-lg bg-white/5 hover:bg-white/10 border border-white/5 hover:border-white/20 transition-all disabled:opacity-50"
        >
            <div className="font-bold text-foreground">{label}</div>
            <div className="text-xs text-muted-foreground">{desc}</div>
        </button>
    )
}
