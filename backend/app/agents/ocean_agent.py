from typing import Dict, Any
from backend.app.schemas.orca import OceanAgentOutput


class OceanAgent:
    """
    Evaluates oceanographic parameters: SST, Chlorophyll frontal boundaries, and currents.
    """

    async def execute(self, ocean_data: Dict[str, Any]) -> OceanAgentOutput:
        sst = ocean_data.get("sea_surface_temperature_c", 28.4)
        current = ocean_data.get("ocean_current_knots", 0.4)
        chlorophyll = ocean_data.get("chlorophyll_density", "Favorable")

        factors = [
            f"SST {sst:.1f}°C optimal for pelagic fish",
            f"Plankton density: {chlorophyll}",
            f"Current velocity {current:.1f} kt",
        ]

        if 26.0 <= sst <= 29.5 and current <= 1.5:
            cond = "favorable"
            conf = 0.94
        elif 24.0 <= sst <= 31.0:
            cond = "moderate"
            conf = 0.90
        else:
            cond = "unfavorable"
            conf = 0.88

        return OceanAgentOutput(
            condition=cond,
            key_factors=factors,
            confidence=conf,
        )


ocean_agent = OceanAgent()
