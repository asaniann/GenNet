'use client'

import React, { useCallback } from 'react'
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
} from 'react-flow-renderer'

interface NetworkEditorProps {
  initialNodes?: Node[]
  initialEdges?: Edge[]
  onSave?: (nodes: Node[], edges: Edge[]) => void
}

export function NetworkEditor({ initialNodes = [], initialEdges = [], onSave }: NetworkEditorProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes)
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges)

  const onConnect = useCallback(
    (params: Connection) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  )

  const handleSave = useCallback(() => {
    if (onSave) {
      onSave(nodes, edges)
    }
  }, [nodes, edges, onSave])

  return (
    <div className="w-full h-screen">
      <div className="absolute top-4 right-4 z-10">
        <button
          onClick={handleSave}
          className="px-4 py-2 bg-primary-600 text-white rounded hover:bg-primary-700"
        >
          Save Network
        </button>
      </div>
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onConnect={onConnect}
        fitView
      >
        <Background />
        <Controls />
        <MiniMap />
      </ReactFlow>
    </div>
  )
}

