"""
Splunk Monitoring Configuration
HTTP Event Collector (HEC) integration for logging and analytics.
"""

import json
import logging
import aiohttp
from typing import Dict, Any, Optional
from datetime import datetime

import os

# Configuration can be loaded from environment variables when used standalone
class SplunkSettings:
    """Splunk configuration settings."""
    SPLUNK_HEC_URL = os.getenv("SPLUNK_HEC_URL")
    SPLUNK_HEC_TOKEN = os.getenv("SPLUNK_HEC_TOKEN")

settings = SplunkSettings()

logger = logging.getLogger(__name__)


class SplunkHECClient:
    """
    Splunk HTTP Event Collector client for sending logs and metrics.

    Usage:
        client = SplunkHECClient()
        await client.send_event({
            "event": "eligibility_check",
            "session_id": "abc123",
            "result": "eligible"
        })
    """

    def __init__(
        self,
        hec_url: Optional[str] = None,
        hec_token: Optional[str] = None
    ):
        self.hec_url = hec_url or settings.SPLUNK_HEC_URL
        self.hec_token = hec_token or settings.SPLUNK_HEC_TOKEN
        self._session: Optional[aiohttp.ClientSession] = None

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                headers={
                    "Authorization": f"Splunk {self.hec_token}",
                    "Content-Type": "application/json"
                }
            )
        return self._session

    async def send_event(
        self,
        event_data: Dict[str, Any],
        source: str = "loan-eligibility-agent",
        sourcetype: str = "json",
        index: str = "main"
    ) -> bool:
        """
        Send an event to Splunk HEC.

        Args:
            event_data: The event data to send
            source: Source identifier
            sourcetype: Splunk sourcetype
            index: Target Splunk index

        Returns:
            True if successful, False otherwise
        """
        if not self.hec_url or not self.hec_token:
            logger.warning("Splunk HEC not configured, skipping event")
            return False

        payload = {
            "time": datetime.utcnow().timestamp(),
            "source": source,
            "sourcetype": sourcetype,
            "index": index,
            "event": event_data
        }

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.hec_url}/services/collector/event",
                json=payload,
                ssl=False  # Set to True in production with proper certs
            ) as response:
                if response.status == 200:
                    return True
                else:
                    logger.error(f"Splunk HEC error: {response.status}")
                    return False
        except Exception as e:
            logger.error(f"Failed to send to Splunk: {e}")
            return False

    async def send_metric(
        self,
        metric_name: str,
        value: float,
        dimensions: Optional[Dict[str, str]] = None
    ) -> bool:
        """
        Send a metric to Splunk.

        Args:
            metric_name: Name of the metric
            value: Metric value
            dimensions: Additional dimensions/tags

        Returns:
            True if successful, False otherwise
        """
        event_data = {
            "metric_name": metric_name,
            "value": value,
            "dimensions": dimensions or {},
            "_time": datetime.utcnow().timestamp()
        }
        return await self.send_event(
            event_data,
            sourcetype="metrics"
        )

    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()


# Dashboard queries for Splunk
SPLUNK_DASHBOARD_QUERIES = {
    "eligibility_decisions": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.decision
        | stats count by event.decision
        | rename event.decision as "Decision"
    """,

    "decisions_over_time": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.decision
        | timechart span=1h count by event.decision
    """,

    "loan_types_distribution": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.loan_type
        | stats count by event.loan_type
        | rename event.loan_type as "Loan Type"
    """,

    "average_response_time": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.response_time_ms
        | stats avg(event.response_time_ms) as "Avg Response Time (ms)"
    """,

    "response_time_percentiles": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.response_time_ms
        | stats
            perc50(event.response_time_ms) as p50,
            perc90(event.response_time_ms) as p90,
            perc99(event.response_time_ms) as p99
    """,

    "handoff_requests": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.handoff_reason
        | stats count by event.handoff_reason
        | sort - count
    """,

    "error_rate": """
        index=main sourcetype=json source="loan-eligibility-agent" level=ERROR
        | timechart span=1h count as "Errors"
    """,

    "active_sessions": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.session_id
        | dedup event.session_id
        | timechart span=1h dc(event.session_id) as "Active Sessions"
    """,

    "approval_rate": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.decision
        | stats
            count(eval(event.decision="eligible" OR event.decision="conditionally_eligible")) as approved,
            count as total
        | eval approval_rate = round((approved/total)*100, 2)
        | fields approval_rate
    """,

    "credit_score_distribution": """
        index=main sourcetype=json source="loan-eligibility-agent"
        | spath event.factors{}.details.score
        | where isnotnull('event.factors{}.details.score')
        | eval score_range = case(
            'event.factors{}.details.score' >= 750, "Excellent (750+)",
            'event.factors{}.details.score' >= 700, "Good (700-749)",
            'event.factors{}.details.score' >= 650, "Fair (650-699)",
            true(), "Needs Improvement (<650)"
          )
        | stats count by score_range
    """
}


# Dashboard definition for export
SPLUNK_DASHBOARD_XML = """
<dashboard version="1.1" theme="dark">
  <label>Loan Eligibility Agent Dashboard</label>
  <description>Real-time monitoring of loan pre-qualification conversational agent</description>

  <row>
    <panel>
      <title>Eligibility Decisions - Last 24 Hours</title>
      <chart>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-24h
          | spath event.decision
          | stats count by event.decision</query>
        </search>
        <option name="charting.chart">pie</option>
      </chart>
    </panel>
    <panel>
      <title>Decisions Over Time</title>
      <chart>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-24h
          | spath event.decision
          | timechart span=1h count by event.decision</query>
        </search>
        <option name="charting.chart">area</option>
        <option name="charting.chart.stackMode">stacked</option>
      </chart>
    </panel>
  </row>

  <row>
    <panel>
      <title>Response Time (ms)</title>
      <single>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-1h
          | spath event.response_time_ms
          | stats avg(event.response_time_ms) as avg_time
          | eval avg_time = round(avg_time, 0)</query>
        </search>
        <option name="unit">ms</option>
      </single>
    </panel>
    <panel>
      <title>Active Sessions</title>
      <single>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-1h
          | spath event.session_id
          | stats dc(event.session_id) as sessions</query>
        </search>
      </single>
    </panel>
    <panel>
      <title>Approval Rate</title>
      <single>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-24h
          | spath event.decision
          | stats count(eval(event.decision="eligible" OR event.decision="conditionally_eligible")) as approved, count as total
          | eval rate = round((approved/total)*100, 1)
          | fields rate</query>
        </search>
        <option name="unit">%</option>
      </single>
    </panel>
    <panel>
      <title>Human Handoffs</title>
      <single>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-24h event.handoff_reason=*
          | stats count</query>
        </search>
      </single>
    </panel>
  </row>

  <row>
    <panel>
      <title>Loan Types Distribution</title>
      <chart>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" earliest=-7d
          | spath event.loan_type
          | stats count by event.loan_type</query>
        </search>
        <option name="charting.chart">bar</option>
      </chart>
    </panel>
    <panel>
      <title>Error Rate</title>
      <chart>
        <search>
          <query>index=main sourcetype=json source="loan-eligibility-agent" level=ERROR earliest=-24h
          | timechart span=1h count as Errors</query>
        </search>
        <option name="charting.chart">line</option>
      </chart>
    </panel>
  </row>
</dashboard>
"""
