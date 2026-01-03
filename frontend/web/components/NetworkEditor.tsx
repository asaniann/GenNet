'use client'

import React, { useCallback, useState, useMemo, useRef } from 'react'
import ReactFlow, {
  Node,
  Edge,
  addEdge,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  Connection,
  MarkerType,
  NodeTypes,
  EdgeTypes,
  ReactFlowInstance,
  BackgroundVariant,
} from 'react-flow-renderer'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { Select } from '@/components/ui/Select'
import { Modal } from '@/components/ui/Modal'
import { Card, CardBody, CardHeader } from '@/components/ui/Card'
import { Badge } from '@/components/ui/Badge'
import { Toggle } from '@/components/ui/Toggle'
import { useToast } from '@/components/ui/Toast'

// Custom node component for gene nodes
const GeneNode = ({ data, selected }: { data: any; selected: boolean }) => {
  const getNodeColor = (type: string) => {
    switch (type) {
      case 'transcription_factor':
        return 'bg-blue-500 border-blue-600'
      case 'target_gene':
        return 'bg-green-500 border-green-600'
      case 'signaling':
        return 'bg-purple-500 border-purple-600'
      case 'receptor':
        return 'bg-amber-500 border-amber-600'
      default:
        return 'bg-slate-500 border-slate-600'
    }
  }

  return (
    <div
      className={`px-4 py-2 rounded-lg border-2 shadow-lg min-w-[100px] text-center transition-all
        ${getNodeColor(data.geneType || 'default')}
        ${selected ? 'ring-2 ring-offset-2 ring-blue-400 scale-105' : ''}
      `}
    >
      <div className="text-white font-semibold text-sm">{data.label}</div>
      {data.geneType && (
        <div className="text-white/70 text-xs mt-1 capitalize">
          {data.geneType.replace('_', ' ')}
        </div>
      )}
      {data.expression !== undefined && (
        <div className={`text-xs mt-1 font-mono ${data.expression > 0 ? 'text-green-200' : 'text-red-200'}`}>
          {data.expression > 0 ? '↑' : '↓'} {Math.abs(data.expression).toFixed(2)}
        </div>
      )}
    </div>
  )
}

// Custom edge for regulatory interactions
const RegulationEdge = ({ 
  id, 
  sourceX, 
  sourceY, 
  targetX, 
  targetY, 
  data,
  style = {},
  markerEnd 
}: any) => {
  const edgeColor = data?.regulation === 'activation' ? '#22c55e' : data?.regulation === 'inhibition' ? '#ef4444' : '#94a3b8'
  const strokeWidth = data?.weight ? Math.max(1, Math.min(4, data.weight * 2)) : 2
  
  const edgePath = `M${sourceX},${sourceY} C${sourceX + (targetX - sourceX) / 2},${sourceY} ${sourceX + (targetX - sourceX) / 2},${targetY} ${targetX},${targetY}`
  
  return (
    <g className="react-flow__edge">
      <path
        id={id}
        style={{
          ...style,
          stroke: edgeColor,
          strokeWidth,
        }}
        className="react-flow__edge-path"
        d={edgePath}
        markerEnd={markerEnd}
      />
      {data?.label && (
        <text>
          <textPath
            href={`#${id}`}
            style={{ fontSize: 10, fill: edgeColor }}
            startOffset="50%"
            textAnchor="middle"
          >
            {data.label}
          </textPath>
        </text>
      )}
    </g>
  )
}

const nodeTypes: NodeTypes = {
  gene: GeneNode,
}

const edgeTypes: EdgeTypes = {
  regulation: RegulationEdge,
}

interface NetworkEditorProps {
  initialNodes?: Node[]
  initialEdges?: Edge[]
  networkId?: string
  networkName?: string
  readOnly?: boolean
  onSave?: (nodes: Node[], edges: Edge[]) => void
  onNodesChange?: (nodes: Node[]) => void
  onEdgesChange?: (edges: Edge[]) => void
}

export function NetworkEditor({ 
  initialNodes = [], 
  initialEdges = [], 
  networkId,
  networkName = 'Network',
  readOnly = false,
  onSave,
  onNodesChange: onNodesChangeCallback,
  onEdgesChange: onEdgesChangeCallback,
}: NetworkEditorProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)
  const [reactFlowInstance, setReactFlowInstance] = useState<ReactFlowInstance | null>(null)
  
  // UI State
  const [showMiniMap, setShowMiniMap] = useState(true)
  const [showGrid, setShowGrid] = useState(true)
  const [gridType, setGridType] = useState<BackgroundVariant>(BackgroundVariant.Dots)
  const [snapToGrid, setSnapToGrid] = useState(true)
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [selectedEdge, setSelectedEdge] = useState<Edge | null>(null)
  
  // Modal State
  const [nodeModalOpen, setNodeModalOpen] = useState(false)
  const [edgeModalOpen, setEdgeModalOpen] = useState(false)
  const [editingNode, setEditingNode] = useState<Node | null>(null)
  const [editingEdge, setEditingEdge] = useState<Edge | null>(null)
  
  // Form State
  const [nodeForm, setNodeForm] = useState({
    label: '',
    geneType: 'target_gene',
    expression: 0,
  })
  const [edgeForm, setEdgeForm] = useState({
    regulation: 'activation',
    weight: 1,
    label: '',
  })
  
  const { addToast } = useToast()
  const fileInputRef = useRef<HTMLInputElement>(null)

  const onConnect = useCallback(
    (params: Connection) => {
      if (readOnly) return
      
      const newEdge = {
        ...params,
        type: 'regulation',
        data: { regulation: 'activation', weight: 1 },
        markerEnd: {
          type: MarkerType.ArrowClosed,
          color: '#22c55e',
        },
      }
      setEdges((eds) => addEdge(newEdge, eds))
      onEdgesChangeCallback?.(edges)
    },
    [setEdges, readOnly, edges, onEdgesChangeCallback]
  )

  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(nodes, edges)
      addToast({
        type: 'success',
        title: 'Network Saved',
        message: 'Your network has been saved successfully.',
      })
    }
  }, [nodes, edges, onSave, addToast])

  const handleAddNode = useCallback(() => {
    if (readOnly) return
    setEditingNode(null)
    setNodeForm({ label: '', geneType: 'target_gene', expression: 0 })
    setNodeModalOpen(true)
  }, [readOnly])

  const handleEditNode = useCallback((node: Node) => {
    if (readOnly) return
    setEditingNode(node)
    setNodeForm({
      label: node.data.label || '',
      geneType: node.data.geneType || 'target_gene',
      expression: node.data.expression || 0,
    })
    setNodeModalOpen(true)
  }, [readOnly])

  const handleSaveNode = useCallback(() => {
    if (!nodeForm.label.trim()) {
      addToast({ type: 'error', title: 'Error', message: 'Node label is required' })
      return
    }

    if (editingNode) {
      // Update existing node
      setNodes((nds) =>
        nds.map((n) =>
          n.id === editingNode.id
            ? { ...n, data: { ...n.data, ...nodeForm } }
            : n
        )
      )
    } else {
      // Add new node
      const position = reactFlowInstance?.project({ 
        x: window.innerWidth / 2, 
        y: window.innerHeight / 2 
      }) || { x: 250, y: 250 }
      
      const newNode: Node = {
        id: `node-${Date.now()}`,
        type: 'gene',
        position,
        data: nodeForm,
      }
      setNodes((nds) => [...nds, newNode])
    }
    
    setNodeModalOpen(false)
    onNodesChangeCallback?.(nodes)
  }, [nodeForm, editingNode, setNodes, reactFlowInstance, nodes, onNodesChangeCallback, addToast])

  const handleDeleteNode = useCallback((nodeId: string) => {
    if (readOnly) return
    setNodes((nds) => nds.filter((n) => n.id !== nodeId))
    setEdges((eds) => eds.filter((e) => e.source !== nodeId && e.target !== nodeId))
    setSelectedNode(null)
    addToast({ type: 'info', title: 'Node Deleted', message: 'The node has been removed.' })
  }, [setNodes, setEdges, readOnly, addToast])

  const handleEditEdge = useCallback((edge: Edge) => {
    if (readOnly) return
    setEditingEdge(edge)
    setEdgeForm({
      regulation: edge.data?.regulation || 'activation',
      weight: edge.data?.weight || 1,
      label: edge.data?.label || '',
    })
    setEdgeModalOpen(true)
  }, [readOnly])

  const handleSaveEdge = useCallback(() => {
    if (!editingEdge) return

    setEdges((eds) =>
      eds.map((e) =>
        e.id === editingEdge.id
          ? {
              ...e,
              data: { ...e.data, ...edgeForm },
              markerEnd: {
                type: MarkerType.ArrowClosed,
                color: edgeForm.regulation === 'activation' ? '#22c55e' : '#ef4444',
              },
            }
          : e
      )
    )
    setEdgeModalOpen(false)
    onEdgesChangeCallback?.(edges)
  }, [edgeForm, editingEdge, setEdges, edges, onEdgesChangeCallback])

  const handleDeleteEdge = useCallback((edgeId: string) => {
    if (readOnly) return
    setEdges((eds) => eds.filter((e) => e.id !== edgeId))
    setSelectedEdge(null)
    addToast({ type: 'info', title: 'Edge Deleted', message: 'The connection has been removed.' })
  }, [setEdges, readOnly, addToast])

  const handleExport = useCallback((format: 'json' | 'png' | 'svg') => {
    if (format === 'json') {
      const data = { nodes, edges, networkId, networkName }
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `${networkName.replace(/\s+/g, '_')}.json`
      link.click()
      URL.revokeObjectURL(url)
      addToast({ type: 'success', title: 'Exported', message: 'Network exported as JSON' })
    } else {
      addToast({ type: 'info', title: 'Export', message: `${format.toUpperCase()} export coming soon` })
    }
  }, [nodes, edges, networkId, networkName, addToast])

  const handleImport = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0]
    if (!file) return

    const reader = new FileReader()
    reader.onload = (e) => {
      try {
        const data = JSON.parse(e.target?.result as string)
        if (data.nodes && data.edges) {
          setNodes(data.nodes)
          setEdges(data.edges)
          addToast({ type: 'success', title: 'Imported', message: 'Network imported successfully' })
        }
      } catch (err) {
        addToast({ type: 'error', title: 'Error', message: 'Failed to import network' })
      }
    }
    reader.readAsText(file)
  }, [setNodes, setEdges, addToast])

  const handleZoomFit = useCallback(() => {
    reactFlowInstance?.fitView({ padding: 0.2 })
  }, [reactFlowInstance])

  const handleCenterView = useCallback(() => {
    reactFlowInstance?.setCenter(0, 0, { zoom: 1 })
  }, [reactFlowInstance])

  const stats = useMemo(() => ({
    nodes: nodes.length,
    edges: edges.length,
    activations: edges.filter((e) => e.data?.regulation === 'activation').length,
    inhibitions: edges.filter((e) => e.data?.regulation === 'inhibition').length,
  }), [nodes, edges])

  return (
    <div className="w-full h-full relative bg-slate-50 dark:bg-slate-900">
      {/* Top Toolbar */}
      <div className="absolute top-4 left-4 right-4 z-10 flex items-center justify-between gap-4">
        {/* Left Section - Title and Stats */}
        <Card padding="sm" className="flex items-center gap-4">
          <div>
            <h2 className="font-semibold text-slate-900 dark:text-slate-100">{networkName}</h2>
            <div className="flex items-center gap-3 text-xs text-slate-500 dark:text-slate-400">
              <span>{stats.nodes} nodes</span>
              <span>•</span>
              <span>{stats.edges} edges</span>
              <span>•</span>
              <span className="text-green-600">{stats.activations} ↑</span>
              <span className="text-red-600">{stats.inhibitions} ↓</span>
            </div>
          </div>
        </Card>

        {/* Right Section - Actions */}
        <div className="flex items-center gap-2">
          {!readOnly && (
            <>
              <Button onClick={handleAddNode} size="sm">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                </svg>
                Add Node
              </Button>
              <Button onClick={handleSave} size="sm" variant="primary">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7H5a2 2 0 00-2 2v9a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-3m-1 4l-3 3m0 0l-3-3m3 3V4" />
                </svg>
                Save
              </Button>
            </>
          )}
          <input
            ref={fileInputRef}
            type="file"
            accept=".json"
            className="hidden"
            onChange={handleImport}
          />
          <Button variant="secondary" size="sm" onClick={() => fileInputRef.current?.click()}>
            Import
          </Button>
          <Button variant="secondary" size="sm" onClick={() => handleExport('json')}>
            Export
          </Button>
        </div>
      </div>

      {/* Left Sidebar - View Controls */}
      <div className="absolute top-20 left-4 z-10">
        <Card padding="sm" className="w-48 space-y-3">
          <div className="text-xs font-medium text-slate-500 dark:text-slate-400 uppercase tracking-wider">
            View Options
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-700 dark:text-slate-300">Mini Map</span>
            <Toggle checked={showMiniMap} onChange={setShowMiniMap} size="sm" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-700 dark:text-slate-300">Grid</span>
            <Toggle checked={showGrid} onChange={setShowGrid} size="sm" />
          </div>
          <div className="flex items-center justify-between">
            <span className="text-sm text-slate-700 dark:text-slate-300">Snap to Grid</span>
            <Toggle checked={snapToGrid} onChange={setSnapToGrid} size="sm" />
          </div>
          <Select
            label="Grid Style"
            options={[
              { value: 'dots', label: 'Dots' },
              { value: 'lines', label: 'Lines' },
              { value: 'cross', label: 'Cross' },
            ]}
            value={gridType}
            onChange={(v) => setGridType(v as BackgroundVariant)}
            className="mt-2"
          />
          <div className="pt-2 border-t border-slate-200 dark:border-slate-700 space-y-2">
            <Button variant="ghost" size="sm" onClick={handleZoomFit} className="w-full justify-start">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
              Fit View
            </Button>
            <Button variant="ghost" size="sm" onClick={handleCenterView} className="w-full justify-start">
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
              </svg>
              Center
            </Button>
          </div>
        </Card>
      </div>

      {/* Right Sidebar - Node/Edge Properties */}
      {(selectedNode || selectedEdge) && !readOnly && (
        <div className="absolute top-20 right-4 z-10">
          <Card padding="sm" className="w-64">
            {selectedNode && (
              <>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-900 dark:text-slate-100">Node Properties</span>
                    <button
                      onClick={() => setSelectedNode(null)}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </CardHeader>
                <CardBody className="space-y-3">
                  <div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">Label</span>
                    <p className="font-medium text-slate-900 dark:text-slate-100">{selectedNode.data.label}</p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">Type</span>
                    <p className="capitalize text-slate-700 dark:text-slate-300">
                      {selectedNode.data.geneType?.replace('_', ' ') || 'Unknown'}
                    </p>
                  </div>
                  {selectedNode.data.expression !== undefined && (
                    <div>
                      <span className="text-xs text-slate-500 dark:text-slate-400">Expression</span>
                      <p className={selectedNode.data.expression > 0 ? 'text-green-600' : 'text-red-600'}>
                        {selectedNode.data.expression > 0 ? '↑' : '↓'} {Math.abs(selectedNode.data.expression).toFixed(2)}
                      </p>
                    </div>
                  )}
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" variant="secondary" onClick={() => handleEditNode(selectedNode)} className="flex-1">
                      Edit
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => handleDeleteNode(selectedNode.id)} className="flex-1">
                      Delete
                    </Button>
                  </div>
                </CardBody>
              </>
            )}
            {selectedEdge && (
              <>
                <CardHeader className="pb-2">
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-slate-900 dark:text-slate-100">Edge Properties</span>
                    <button
                      onClick={() => setSelectedEdge(null)}
                      className="text-slate-400 hover:text-slate-600 dark:hover:text-slate-300"
                    >
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                      </svg>
                    </button>
                  </div>
                </CardHeader>
                <CardBody className="space-y-3">
                  <div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">Regulation Type</span>
                    <Badge variant={selectedEdge.data?.regulation === 'activation' ? 'success' : 'danger'}>
                      {selectedEdge.data?.regulation === 'activation' ? '↑ Activation' : '↓ Inhibition'}
                    </Badge>
                  </div>
                  <div>
                    <span className="text-xs text-slate-500 dark:text-slate-400">Weight</span>
                    <p className="font-medium text-slate-900 dark:text-slate-100">{selectedEdge.data?.weight || 1}</p>
                  </div>
                  <div className="flex gap-2 pt-2">
                    <Button size="sm" variant="secondary" onClick={() => handleEditEdge(selectedEdge)} className="flex-1">
                      Edit
                    </Button>
                    <Button size="sm" variant="danger" onClick={() => handleDeleteEdge(selectedEdge.id)} className="flex-1">
                      Delete
                    </Button>
                  </div>
                </CardBody>
              </>
            )}
          </Card>
        </div>
      )}

      {/* React Flow Canvas */}
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        onInit={setReactFlowInstance}
        onNodeClick={(_, node) => {
          setSelectedNode(node)
          setSelectedEdge(null)
        }}
        onNodeDoubleClick={(_, node) => handleEditNode(node)}
        onEdgeClick={(_, edge) => {
          setSelectedEdge(edge)
          setSelectedNode(null)
        }}
        onEdgeDoubleClick={(_, edge) => handleEditEdge(edge)}
        onPaneClick={() => {
          setSelectedNode(null)
          setSelectedEdge(null)
        }}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        snapToGrid={snapToGrid}
        snapGrid={[15, 15]}
        fitView
        attributionPosition="bottom-left"
        className="bg-slate-50 dark:bg-slate-900"
      >
        {showGrid && (
          <Background 
            variant={gridType} 
            gap={16} 
            size={1}
            color={gridType === BackgroundVariant.Dots ? '#94a3b8' : '#e2e8f0'}
          />
        )}
        <Controls 
          className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
        />
        {showMiniMap && (
          <MiniMap 
            className="bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden"
            nodeColor={(node) => {
              switch (node.data?.geneType) {
                case 'transcription_factor': return '#3b82f6'
                case 'target_gene': return '#22c55e'
                case 'signaling': return '#a855f7'
                case 'receptor': return '#f59e0b'
                default: return '#64748b'
              }
            }}
          />
        )}
      </ReactFlow>

      {/* Node Edit Modal */}
      <Modal
        isOpen={nodeModalOpen}
        onClose={() => setNodeModalOpen(false)}
        title={editingNode ? 'Edit Node' : 'Add New Node'}
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setNodeModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveNode}>
              {editingNode ? 'Update' : 'Add'} Node
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Input
            label="Gene Name"
            placeholder="e.g., TP53, BRCA1"
            value={nodeForm.label}
            onChange={(e) => setNodeForm({ ...nodeForm, label: e.target.value })}
          />
          <Select
            label="Node Type"
            options={[
              { value: 'target_gene', label: 'Target Gene' },
              { value: 'transcription_factor', label: 'Transcription Factor' },
              { value: 'signaling', label: 'Signaling Molecule' },
              { value: 'receptor', label: 'Receptor' },
            ]}
            value={nodeForm.geneType}
            onChange={(v) => setNodeForm({ ...nodeForm, geneType: v })}
          />
          <Input
            label="Expression Level"
            type="number"
            step="0.1"
            placeholder="0"
            value={nodeForm.expression.toString()}
            onChange={(e) => setNodeForm({ ...nodeForm, expression: parseFloat(e.target.value) || 0 })}
            hint="Positive for upregulated, negative for downregulated"
          />
        </div>
      </Modal>

      {/* Edge Edit Modal */}
      <Modal
        isOpen={edgeModalOpen}
        onClose={() => setEdgeModalOpen(false)}
        title="Edit Connection"
        size="sm"
        footer={
          <>
            <Button variant="secondary" onClick={() => setEdgeModalOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleSaveEdge}>
              Update Connection
            </Button>
          </>
        }
      >
        <div className="space-y-4">
          <Select
            label="Regulation Type"
            options={[
              { value: 'activation', label: '↑ Activation (Promotes)' },
              { value: 'inhibition', label: '↓ Inhibition (Suppresses)' },
            ]}
            value={edgeForm.regulation}
            onChange={(v) => setEdgeForm({ ...edgeForm, regulation: v })}
          />
          <Input
            label="Weight"
            type="number"
            step="0.1"
            min="0"
            max="5"
            value={edgeForm.weight.toString()}
            onChange={(e) => setEdgeForm({ ...edgeForm, weight: parseFloat(e.target.value) || 1 })}
            hint="Strength of the regulatory interaction (0-5)"
          />
          <Input
            label="Label (Optional)"
            placeholder="e.g., phosphorylation"
            value={edgeForm.label}
            onChange={(e) => setEdgeForm({ ...edgeForm, label: e.target.value })}
          />
        </div>
      </Modal>
    </div>
  )
}

