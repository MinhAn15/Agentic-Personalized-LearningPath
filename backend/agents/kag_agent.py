import logging
from typing import Dict, Any, List, Tuple
from datetime import datetime
from statistics import mean, stdev

from backend.core.base_agent import BaseAgent, AgentType
from backend.config import get_settings

logger = logging.getLogger(__name__)

class KAGAgent(BaseAgent):
    """
    KAG Agent - Knowledge Graph Aggregator.
    
    Merges and analyzes all learner Personal Knowledge Graphs.
    Extracts system-wide patterns and recommends course improvements.
    
    Responsibility:
    - Retrieve all learner Personal KGs
    - Merge into aggregated view
    - Calculate statistics (average mastery, difficulty, etc.)
    - Identify difficult concepts
    - Find common misconceptions
    - Analyze prerequisite impact
    - Generate course recommendations
    - Predict intervention points
    
    Process Flow:
    1. Get all learner Personal KGs from database
    2. Merge into aggregated knowledge graph
    3. Calculate statistics (mean, stdev, etc.)
    4. Identify patterns:
       - Difficult concepts (low average mastery)
       - Common misconceptions (error clusters)
       - Prerequisite impact (correlation analysis)
       - Success factors (what helps?)
    5. Generate insights
    6. Recommend course improvements
    7. Predict intervention points
    
    Example:
        Analysis of 100 learners:
        - WHERE: avg 0.72 mastery (24% struggled)
        - JOIN: avg 0.35 mastery (65% struggled)
        - 60% of JOIN failures had weak WHERE foundation
        
        Insight: Strong WHERE → 90% JOIN success
                 Weak WHERE → 30% JOIN success
        
        Recommendation:
        1. Strengthen WHERE prerequisites
        2. Add WHERE vs JOIN comparison
        3. Delay JOIN until WHERE mastery > 0.8
        4. Add misconception detection for JOIN
    """
    
    def __init__(self, agent_id: str, state_manager, event_bus):
        """
        Initialize KAG Agent.
        
        Args:
            agent_id: Unique agent identifier
            state_manager: Central state manager
            event_bus: Event bus for inter-agent communication
        """
        super().__init__(agent_id, AgentType.KAG, state_manager, event_bus)
        self.logger = logging.getLogger(f"KAGAgent.{agent_id}")
    
    async def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Main execution method - analyze aggregated learner patterns.
        
        Args:
            analysis_depth: str - "shallow" (quick) or "deep" (comprehensive)
            min_learners: int - Minimum learners for pattern to be valid
            
        Returns:
            Dict with analysis and recommendations
        """
        try:
            analysis_depth = kwargs.get("analysis_depth", "shallow")
            min_learners = kwargs.get("min_learners", 10)
            
            self.logger.info(f"📊 Starting KAG analysis (depth={analysis_depth})")
            
            # Step 1: Get all learner Personal KGs
            learner_graphs = await self._retrieve_all_learner_graphs()
            
            if len(learner_graphs) < min_learners:
                return {
                    "success": False,
                    "error": f"Need at least {min_learners} learners, found {len(learner_graphs)}",
                    "agent_id": self.agent_id
                }
            
            self.logger.info(f"Retrieved {len(learner_graphs)} learner graphs")
            
            # Step 2: Merge into aggregated view
            aggregated_graph = await self._merge_graphs(learner_graphs)
            
            # Step 3: Calculate statistics
            statistics = await self._calculate_statistics(aggregated_graph)
            
            # Step 4: Identify patterns
            patterns = await self._identify_patterns(
                aggregated_graph=aggregated_graph,
                statistics=statistics,
                depth=analysis_depth
            )
            
            # Step 5-7: Generate insights + recommendations + predictions
            insights = patterns.get("insights", [])
            recommendations = await self._generate_recommendations(patterns)
            predictions = await self._predict_interventions(patterns)
            
            result = {
                "success": True,
                "agent_id": self.agent_id,
                "num_learners_analyzed": len(learner_graphs),
                "statistics": statistics,
                "patterns": patterns,
                "insights": insights,
                "recommendations": recommendations,
                "predictions": predictions,
                "timestamp": datetime.now().isoformat()
            }
            
            # Emit event for Knowledge Extraction (to improve course content)
            await self.send_message(
                receiver="knowledge_extraction",
                message_type="kag_analysis_complete",
                payload={
                    "recommendations": recommendations,
                    "difficult_concepts": patterns.get("difficult_concepts", [])
                }
            )
            
            self.logger.info(f"✅ KAG analysis complete: {len(insights)} insights")
            
            return result
        
        except Exception as e:
            self.logger.error(f"❌ KAG analysis failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "agent_id": self.agent_id
            }
    
    async def _retrieve_all_learner_graphs(self) -> List[Dict[str, Any]]:
        """Retrieve all learner Personal Knowledge Graphs"""
        try:
            # In production, query database for all learner KGs
            # For now, return mock structure
            
            return []  # Would be populated from database
        
        except Exception as e:
            self.logger.error(f"Graph retrieval error: {e}")
            return []
    
    async def _merge_graphs(self, learner_graphs: List[Dict]) -> Dict[str, Any]:
        """Merge all learner graphs into aggregated view"""
        try:
            aggregated = {"concepts": {}}
            
            for learner_graph in learner_graphs:
                for concept_id, mastery in learner_graph.items():
                    if concept_id not in aggregated["concepts"]:
                        aggregated["concepts"][concept_id] = {
                            "masteries": [],
                            "errors": [],
                            "misconceptions": []
                        }
                    
                    aggregated["concepts"][concept_id]["masteries"].append(mastery)
            
            return aggregated
        
        except Exception as e:
            self.logger.error(f"Graph merging error: {e}")
            return {"concepts": {}}
    
    async def _calculate_statistics(self, aggregated: Dict) -> Dict[str, Any]:
        """Calculate statistics across all learners"""
        try:
            statistics = {}
            
            for concept_id, data in aggregated.get("concepts", {}).items():
                masteries = data.get("masteries", [])
                
                if masteries:
                    statistics[concept_id] = {
                        "avg_mastery": mean(masteries),
                        "std_dev": stdev(masteries) if len(masteries) > 1 else 0,
                        "min_mastery": min(masteries),
                        "max_mastery": max(masteries),
                        "num_learners": len(masteries),
                        "struggle_rate": len([m for m in masteries if m < 0.5]) / len(masteries)
                    }
            
            return statistics
        
        except Exception as e:
            self.logger.error(f"Statistics calculation error: {e}")
            return {}
    
    async def _identify_patterns(
        self,
        aggregated_graph: Dict,
        statistics: Dict,
        depth: str = "shallow"
    ) -> Dict[str, Any]:
        """Identify patterns and insights"""
        try:
            patterns = {
                "difficult_concepts": [],
                "easy_concepts": [],
                "misconceptions": {},
                "prerequisite_impacts": {},
                "insights": []
            }
            
            # Find difficult concepts (low average mastery)
            for concept_id, stats in statistics.items():
                avg_mastery = stats.get("avg_mastery", 0)
                struggle_rate = stats.get("struggle_rate", 0)
                
                if avg_mastery < 0.4:
                    patterns["difficult_concepts"].append({
                        "concept_id": concept_id,
                        "avg_mastery": avg_mastery,
                        "struggle_rate": struggle_rate
                    })
                    patterns["insights"].append(
                        f"⚠️ {concept_id}: Only {avg_mastery:.0%} mastery, "
                        f"{struggle_rate:.0%} struggle"
                    )
                
                elif avg_mastery > 0.8:
                    patterns["easy_concepts"].append({
                        "concept_id": concept_id,
                        "avg_mastery": avg_mastery
                    })
            
            return patterns
        
        except Exception as e:
            self.logger.error(f"Pattern identification error: {e}")
            return {"insights": []}
    
    async def _generate_recommendations(self, patterns: Dict) -> List[str]:
        """Generate course improvement recommendations"""
        try:
            recommendations = []
            
            for difficult in patterns.get("difficult_concepts", []):
                concept_id = difficult.get("concept_id")
                struggle_rate = difficult.get("struggle_rate", 0)
                
                if struggle_rate > 0.6:
                    recommendations.append(
                        f"📚 Strengthen {concept_id} prerequisites - {struggle_rate:.0%} struggle"
                    )
                    recommendations.append(
                        f"📝 Create comparison tutorial: {concept_id} vs similar concepts"
                    )
                    recommendations.append(
                        f"🎯 Add {concept_id} practice exercises"
                    )
            
            return recommendations
        
        except Exception as e:
            self.logger.error(f"Recommendation generation error: {e}")
            return []
    
    async def _predict_interventions(self, patterns: Dict) -> List[str]:
        """Predict intervention points for next cohort"""
        try:
            predictions = []
            
            for difficult in patterns.get("difficult_concepts", []):
                concept_id = difficult.get("concept_id")
                predictions.append(
                    f"🚀 Next cohort: Allocate 2x time for {concept_id}"
                )
                predictions.append(
                    f"🚩 Flag learners struggling with {concept_id} early"
                )
            
            return predictions
        
        except Exception as e:
            self.logger.error(f"Intervention prediction error: {e}")
            return []
