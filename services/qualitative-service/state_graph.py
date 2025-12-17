"""
State Graph Generator
Generates state graphs from qualitative network parameters
"""

import logging
from typing import List, Dict, Any, Optional, Set, Tuple
from itertools import product

logger = logging.getLogger(__name__)


class StateGraphGenerator:
    """Generate state graphs for qualitative networks"""
    
    def __init__(self):
        pass
    
    def generate_state_graph(
        self,
        network_id: str,
        parameters: Dict[str, Any],
        network_structure: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Generate state graph from parameters
        
        Args:
            network_id: Network identifier
            parameters: K-parameters for the network
            network_structure: Network structure (nodes, edges)
            
        Returns:
            State graph with states and transitions
        """
        try:
            # Extract nodes from network structure or parameters
            nodes = self._extract_nodes(network_structure, parameters)
            
            if not nodes:
                logger.warning("No nodes found, generating empty state graph")
                return {
                    "states": [],
                    "transitions": [],
                    "node_count": 0,
                    "state_count": 0,
                    "transition_count": 0
                }
            
            # Generate all possible states
            states = self._generate_states(nodes)
            
            # Generate transitions between states
            transitions = self._generate_transitions(states, nodes, parameters)
            
            # Analyze state graph properties
            analysis = self._analyze_state_graph(states, transitions)
            
            return {
                "states": states,
                "transitions": transitions,
                "node_count": len(nodes),
                "state_count": len(states),
                "transition_count": len(transitions),
                "analysis": analysis,
                "network_id": network_id
            }
            
        except Exception as e:
            logger.error(f"Error generating state graph: {e}")
            raise
    
    def _extract_nodes(
        self,
        network_structure: Optional[Dict[str, Any]],
        parameters: Dict[str, Any]
    ) -> List[str]:
        """Extract node list from network structure or parameters"""
        nodes = []
        
        if network_structure:
            network_nodes = network_structure.get("nodes", [])
            if network_nodes:
                if isinstance(network_nodes[0], dict):
                    nodes = [node.get("id", node.get("label", "")) for node in network_nodes]
                else:
                    nodes = network_nodes
        
        # Also check parameters for node information
        if not nodes and isinstance(parameters, list):
            for param in parameters:
                node_id = param.get("node_id")
                if node_id and node_id not in nodes:
                    nodes.append(node_id)
        
        return nodes
    
    def _generate_states(self, nodes: List[str]) -> List[Dict[str, Any]]:
        """
        Generate all possible states for the network
        
        In qualitative modeling, each node can be in states: 0 (off) or 1 (on)
        """
        states = []
        
        # Generate all binary combinations
        num_nodes = len(nodes)
        for state_vector in product([0, 1], repeat=num_nodes):
            state = {
                "id": self._state_vector_to_id(state_vector),
                "vector": list(state_vector),
                "node_states": {
                    nodes[i]: state_vector[i] for i in range(num_nodes)
                },
                "label": self._format_state_label(state_vector, nodes)
            }
            states.append(state)
        
        return states
    
    def _state_vector_to_id(self, state_vector: Tuple[int, ...]) -> str:
        """Convert state vector to unique ID"""
        return "".join(map(str, state_vector))
    
    def _format_state_label(self, state_vector: Tuple[int, ...], nodes: List[str]) -> str:
        """Format state label for display"""
        active_nodes = [nodes[i] for i, val in enumerate(state_vector) if val == 1]
        if active_nodes:
            return f"{{{', '.join(active_nodes)}}}"
        else:
            return "{}"
    
    def _generate_transitions(
        self,
        states: List[Dict[str, Any]],
        nodes: List[str],
        parameters: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Generate transitions between states based on qualitative dynamics
        
        Transitions occur when nodes change state according to their K-parameters
        """
        transitions = []
        
        # For each state, determine possible next states
        for from_state in states:
            from_vector = from_state["vector"]
            
            # Determine which nodes can change state
            for to_state in states:
                if from_state["id"] == to_state["id"]:
                    continue  # Skip self-transitions for now
                
                to_vector = to_state["vector"]
                
                # Check if transition is valid
                if self._is_valid_transition(from_vector, to_vector, nodes, parameters):
                    transition = {
                        "from": from_state["id"],
                        "to": to_state["id"],
                        "from_label": from_state["label"],
                        "to_label": to_state["label"],
                        "changed_nodes": self._get_changed_nodes(from_vector, to_vector, nodes),
                        "type": self._classify_transition(from_vector, to_vector)
                    }
                    transitions.append(transition)
        
        return transitions
    
    def _is_valid_transition(
        self,
        from_vector: List[int],
        to_vector: List[int],
        nodes: List[str],
        parameters: Dict[str, Any]
    ) -> bool:
        """
        Check if transition is valid based on qualitative dynamics
        
        A transition is valid if:
        1. Only one node changes state (synchronous transitions)
        2. The change follows the regulatory logic defined by K-parameters
        """
        # Count number of changes
        changes = sum(1 for i in range(len(from_vector)) if from_vector[i] != to_vector[i])
        
        # For simplicity, allow single-node changes
        # In full implementation, this would check against K-parameters
        if changes == 1:
            return True
        
        # Also allow no-change (self-loops handled separately)
        if changes == 0:
            return False
        
        # Multiple simultaneous changes - check if valid
        # This would require checking regulatory logic
        return False  # Conservative: only allow single changes
    
    def _get_changed_nodes(
        self,
        from_vector: List[int],
        to_vector: List[int],
        nodes: List[str]
    ) -> List[str]:
        """Get list of nodes that changed state"""
        changed = []
        for i in range(len(nodes)):
            if from_vector[i] != to_vector[i]:
                changed.append(nodes[i])
        return changed
    
    def _classify_transition(
        self,
        from_vector: List[int],
        to_vector: List[int]
    ) -> str:
        """Classify transition type"""
        changes = sum(1 for i in range(len(from_vector)) if from_vector[i] != to_vector[i])
        
        if changes == 0:
            return "stable"
        elif changes == 1:
            # Check if activation or deactivation
            for i in range(len(from_vector)):
                if from_vector[i] != to_vector[i]:
                    if to_vector[i] > from_vector[i]:
                        return "activation"
                    else:
                        return "deactivation"
        else:
            return "complex"
        
        return "unknown"
    
    def _analyze_state_graph(
        self,
        states: List[Dict[str, Any]],
        transitions: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Analyze state graph properties"""
        # Find cycles
        cycles = self._find_cycles(states, transitions)
        
        # Find attractors (states with no outgoing transitions or cycles)
        attractors = self._find_attractors(states, transitions)
        
        # Calculate reachability
        reachability = self._calculate_reachability(states, transitions)
        
        return {
            "cycles": cycles,
            "attractors": attractors,
            "reachability": reachability,
            "is_connected": self._is_connected(states, transitions)
        }
    
    def _find_cycles(self, states: List[Dict], transitions: List[Dict]) -> List[List[str]]:
        """Find cycles in state graph"""
        # Simplified cycle detection
        # Full implementation would use DFS
        cycles = []
        
        # Build adjacency list
        adj = {state["id"]: [] for state in states}
        for trans in transitions:
            adj[trans["from"]].append(trans["to"])
        
        # Simple cycle detection (find self-loops and small cycles)
        for trans in transitions:
            if trans["from"] == trans["to"]:
                cycles.append([trans["from"]])
        
        return cycles
    
    def _find_attractors(self, states: List[Dict], transitions: List[Dict]) -> List[str]:
        """Find attractor states"""
        # States with no outgoing transitions or in cycles
        outgoing = {state["id"]: 0 for state in states}
        
        for trans in transitions:
            outgoing[trans["from"]] += 1
        
        # Attractors are states with no outgoing transitions
        attractors = [state_id for state_id, count in outgoing.items() if count == 0]
        
        return attractors
    
    def _calculate_reachability(
        self,
        states: List[Dict],
        transitions: List[Dict]
    ) -> Dict[str, List[str]]:
        """Calculate which states are reachable from each state"""
        reachability = {}
        
        # Build adjacency list
        adj = {state["id"]: [] for state in states}
        for trans in transitions:
            adj[trans["from"]].append(trans["to"])
        
        # BFS from each state
        for state in states:
            state_id = state["id"]
            reachable = set()
            queue = [state_id]
            visited = {state_id}
            
            while queue:
                current = queue.pop(0)
                reachable.add(current)
                
                for neighbor in adj.get(current, []):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            
            reachability[state_id] = list(reachable)
        
        return reachability
    
    def _is_connected(self, states: List[Dict], transitions: List[Dict]) -> bool:
        """Check if state graph is connected"""
        if not states:
            return True
        
        # Build adjacency list (undirected for connectivity check)
        adj = {state["id"]: [] for state in states}
        for trans in transitions:
            adj[trans["from"]].append(trans["to"])
            adj[trans["to"]].append(trans["from"])  # Undirected
        
        # BFS from first state
        start = states[0]["id"]
        visited = set()
        queue = [start]
        visited.add(start)
        
        while queue:
            current = queue.pop(0)
            for neighbor in adj.get(current, []):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        
        return len(visited) == len(states)

