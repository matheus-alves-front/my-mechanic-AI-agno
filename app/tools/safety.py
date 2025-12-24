from __future__ import annotations

from typing import Dict
from agno.tools import Toolkit


class SafetyTools(Toolkit):
    def __init__(self) -> None:
        super().__init__(name="safety")
        self.register(self.risk_triage)

    def risk_triage(
        self,
        has_fuel_smell: bool = False,
        has_smoke: bool = False,
        overheating: bool = False,
        brake_failure: bool = False,
        steering_issue: bool = False,
        airbag_light: bool = False,
        high_voltage_vehicle: bool = False,
    ) -> Dict[str, str]:
        """
        Basic safety triage. Agent uses this to decide stop-driving recommendations.
        """
        critical = any([has_fuel_smell, has_smoke, overheating, brake_failure, steering_issue])
        if critical:
            return {
                "severity": "critical",
                "recommendation": "Pare o veículo em local seguro e procure guincho/oficina. Não continue dirigindo.",
            }

        if high_voltage_vehicle and (has_smoke or overheating):
            return {
                "severity": "critical",
                "recommendation": "Veículo híbrido/EV com sinal térmico/fumaça: pare e acione assistência especializada.",
            }

        if airbag_light:
            return {
                "severity": "warning",
                "recommendation": "Luz de airbag acesa: evite viagens longas e diagnostique o sistema (SRS) o quanto antes.",
            }

        return {"severity": "ok", "recommendation": "Sem sinais críticos imediatos. Prossiga com diagnóstico com cautela."}
