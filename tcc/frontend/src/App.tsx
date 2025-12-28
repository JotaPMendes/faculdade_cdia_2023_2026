import { useState } from 'react'
import { Play, FileText, BarChart } from 'lucide-react'
import { cn } from './utils/cn'
import TrainingView from './components/TrainingView'
import ResultsView from './components/ResultsView'
import DocumentationView from './components/DocumentationView'

function App() {
  const [activeTab, setActiveTab] = useState('train')

  const renderContent = () => {
    switch (activeTab) {
      case 'train':
        return <TrainingView />
      case 'results':
        return <ResultsView />
      case 'docs':
        return <DocumentationView />
      default:
        return <TrainingView />
    }
  }

  return (
    <div className="flex h-screen bg-background text-foreground overflow-hidden">
      {/* Sidebar */}
      <aside className="w-64 border-r border-border bg-card flex flex-col">
        <div className="p-6 border-b border-border">
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-600 to-cyan-600 bg-clip-text text-transparent">
            PINN Benchmark
          </h1>
          <p className="text-xs text-muted-foreground mt-1">v2.1.0 • Local Workflow</p>
        </div>

        <nav className="flex-1 p-4 space-y-2">
          <SidebarItem icon={Play} label="Training" active={activeTab === 'train'} onClick={() => setActiveTab('train')} />
          <SidebarItem icon={BarChart} label="Results" active={activeTab === 'results'} onClick={() => setActiveTab('results')} />
          <SidebarItem icon={FileText} label="Documentation" active={activeTab === 'docs'} onClick={() => setActiveTab('docs')} />
        </nav>
      </aside>

      {/* Main Content */}
      <main className="flex-1 overflow-auto bg-secondary/30">
        {renderContent()}
      </main>
    </div>
  )
}

function SidebarItem({ icon: Icon, label, active, onClick }: any) {
  return (
    <button
      onClick={onClick}
      className={cn(
        "w-full flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all",
        active
          ? "bg-primary/10 text-primary border border-primary/20"
          : "text-muted-foreground hover:bg-secondary hover:text-foreground"
      )}
    >
      <Icon size={18} />
      {label}
    </button>
  )
}

export default App
