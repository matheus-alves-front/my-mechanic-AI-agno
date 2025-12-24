from __future__ import annotations

from typing import Any, Dict, Optional
from agno.tools import Toolkit


class VehicleIntakeTools(Toolkit):
    def __init__(self) -> None:
        super().__init__(name="vehicle_intake")

        self.register(self.collect_profile)

    def collect_profile(
        self,
        brand: str,
        model: str,
        year: int,
        engine: Optional[str] = None,
        mileage_km: Optional[int] = None,
        fuel: Optional[str] = None,
        transmission: Optional[str] = None,
        notes: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Collect minimal vehicle profile for diagnosis context.
        Returns a normalized dict to be stored in session_state by the agent.
        """
        return {
            "brand": brand.strip(),
            "model": model.strip(),
            "year": int(year),
            "engine": (engine or "").strip() or None,
            "mileage_km": int(mileage_km) if mileage_km is not None else None,
            "fuel": (fuel or "").strip() or None,
            "transmission": (transmission or "").strip() or None,
            "notes": (notes or "").strip() or None,
        }
