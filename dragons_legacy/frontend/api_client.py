"""
API client for communicating with the FastAPI backend
"""

import httpx
import asyncio
from typing import Optional, Dict, Any, List


class APIClient:
    """Client for communicating with the Dragons Legacy API."""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.access_token: Optional[str] = None
        
    def _get_headers(self) -> Dict[str, str]:
        """Get headers for API requests."""
        headers = {"Content-Type": "application/json"}
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers
    
    async def get_security_questions(self) -> List[Dict[str, Any]]:
        """Get all available security questions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/security-questions",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def register_user(self, email: str, password: str, 
                          security_question_id: int, security_answer: str) -> Dict[str, Any]:
        """Register a new user."""
        data = {
            "email": email,
            "password": password,
            "security_question_id": security_question_id,
            "security_answer": security_answer
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/register",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def login_user(self, email: str, password: str) -> Dict[str, Any]:
        """Login user and get access token."""
        data = {
            "email": email,
            "password": password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/login",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            result = response.json()
            
            # Store access token
            self.access_token = result["access_token"]
            return result

    async def logout_user(self, email: str) -> Dict[str, Any]:
        """Logout user and clear access token."""
        data = {"email": email}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/logout",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            self.access_token = None
            return response.json()
    
    async def get_user_security_question(self, email: str) -> Dict[str, Any]:
        """Get user's security question for password reset."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/user/{email}/security-question",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()
    
    async def verify_security_answer(self, email: str, security_answer: str) -> Dict[str, Any]:
        """Verify security answer without resetting password."""
        data = {
            "email": email,
            "security_answer": security_answer,
            "new_password": "temp"  # Required by schema but ignored
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/verify-security-answer",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def reset_password(self, email: str, security_answer: str, 
                           new_password: str) -> Dict[str, Any]:
        """Reset user password using security question."""
        data = {
            "email": email,
            "security_answer": security_answer,
            "new_password": new_password
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/reset-password",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def create_character(self, email: str, nickname: str, race: str, 
                              gender: str) -> Dict[str, Any]:
        """Create a new character."""
        data = {
            "email": email,
            "nickname": nickname,
            "race": race,
            "gender": gender
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/characters",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_character_by_email(self, email: str) -> Dict[str, Any]:
        """Get a user's character data by email."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/characters/by-email/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def travel(self, email: str, destination: str) -> Dict[str, Any]:
        """Travel to an adjacent region."""
        data = {
            "email": email,
            "destination": destination
        }
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/characters/travel",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_region_info(self, region_name: str) -> Dict[str, Any]:
        """Get region info including connected regions."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/world/regions/{region_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_region_npcs(self, region_name: str) -> List[Dict[str, Any]]:
        """Get NPCs in a specific region."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/world/npcs/{region_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_all_items(self) -> List[Dict[str, Any]]:
        """Get the complete item catalog."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/items",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_inventory(self, email: str) -> List[Dict[str, Any]]:
        """Get the player's inventory from the server."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/inventory/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def add_inventory_item(self, email: str, item_catalog_id: int) -> Dict[str, Any]:
        """Add an item to the player's inventory on the server."""
        data = {"email": email, "item_catalog_id": item_catalog_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/add",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def delete_inventory_item(self, email: str, instance_id: int) -> Dict[str, Any]:
        """Delete an item instance from the player's inventory on the server."""
        data = {"email": email, "instance_id": instance_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/delete",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def equip_item(self, email: str, instance_id: int) -> Dict[str, Any]:
        """Equip an item to the character."""
        data = {"email": email, "instance_id": instance_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/equip",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def unequip_item(self, email: str, instance_id: int) -> Dict[str, Any]:
        """Unequip an item from the character."""
        data = {"email": email, "instance_id": instance_id}
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/inventory/unequip",
                json=data,
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_character_stats(self, email: str) -> Dict[str, Any]:
        """Get character stats including base stats and item bonuses."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/characters/by-email/{email}/stats",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_players_on_map(self, map_name: str) -> Dict[str, Any]:
        """Get list of online players on a specific map."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/world/players-on-map/{map_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def view_character_by_nickname(self, nickname: str) -> Dict[str, Any]:
        """View another player's character info by nickname."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/characters/view/{nickname}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_region_mobs(self, region_name: str) -> List[Dict[str, Any]]:
        """Get mobs available in a specific region."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/world/mobs/{region_name}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_active_fight(self, email: str) -> Optional[Dict[str, Any]]:
        """Check if the player has an active fight. Returns fight info or None."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fight/active/{email}",
                headers=self._get_headers()
            )
            if response.status_code == 404:
                return None
            response.raise_for_status()
            return response.json()

    async def get_fight_history(self, email: str) -> List[Dict[str, Any]]:
        """Get all fight statistics for a character."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fight-history/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_fight_stat_detail(self, email: str, stat_id: int) -> Dict[str, Any]:
        """Get a single fight statistic by ID."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/fight-history/{email}/{stat_id}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    # ----------------------------------------------------------
    # Bag
    # ----------------------------------------------------------

    async def get_bag(self, email: str) -> List[Dict[str, Any]]:
        """Get the character's bag (2 slots)."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/bag/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def add_to_bag(self, email: str, item_catalog_id: int, quantity: int, slot_index: int) -> Dict[str, Any]:
        """Move consumable items from inventory into a bag slot."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bag/add",
                params={
                    "email": email,
                    "item_catalog_id": item_catalog_id,
                    "quantity": quantity,
                    "slot_index": slot_index,
                },
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def remove_from_bag(self, email: str, slot_index: int) -> Dict[str, Any]:
        """Remove all items from a bag slot back to inventory."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bag/remove",
                params={"email": email, "slot_index": slot_index},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def use_bag_item_in_fight(self, email: str, slot_index: int) -> Dict[str, Any]:
        """Use one charge of a bag slot item during a fight."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/bag/use-in-fight",
                params={"email": email, "slot_index": slot_index},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    # ----------------------------------------------------------
    # Combos
    # ----------------------------------------------------------

    async def get_combos(self, email: str) -> List[Dict[str, Any]]:
        """Get the character's combos."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/combos/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    # ----------------------------------------------------------
    # HP Regeneration & Bread
    # ----------------------------------------------------------

    async def hp_regen_tick(self, email: str) -> Dict[str, Any]:
        """Apply one out-of-combat HP regen tick."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/characters/hp-regen",
                params={"email": email},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def eat_bread(self, email: str) -> Dict[str, Any]:
        """Eat one Bread from inventory."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/characters/eat-bread",
                params={"email": email},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    # ----------------------------------------------------------
    # Quest System
    # ----------------------------------------------------------

    async def get_quests(self, email: str) -> List[Dict[str, Any]]:
        """Get all quests for a character."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/quests/{email}",
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def get_available_quests(self, email: str, npc_name: str) -> List[Dict[str, Any]]:
        """Get quests available from a specific NPC."""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/quests/available/{email}",
                params={"npc_name": npc_name},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def accept_quest(self, email: str, quest_id: str) -> Dict[str, Any]:
        """Accept a quest."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/quests/accept",
                params={"email": email, "quest_id": quest_id},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()

    async def complete_quest(self, email: str, quest_id: str) -> Dict[str, Any]:
        """Complete a quest and claim rewards."""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/quests/complete",
                params={"email": email, "quest_id": quest_id},
                headers=self._get_headers()
            )
            response.raise_for_status()
            return response.json()