"""Static planning data showcased in the dashboard prototype."""

from __future__ import annotations

PLANNER_HOURS = [f"{hour:02d}:00" for hour in range(8, 21)]
_TOTAL_SPAN_MINUTES = 12 * 60  # 08:00 -> 20:00


def _compute_block(start_time: str, end_time: str) -> dict[str, float]:
    """Compute layout information for planning blocks."""
    def to_minutes(value: str) -> int:
        hour, minute = map(int, value.split(":"))
        return hour * 60 + minute

    start = to_minutes(start_time)
    end = to_minutes(end_time)
    top = max(start - 8 * 60, 0)
    duration = max(end - start, 30)
    return {
        "top_pct": (top / _TOTAL_SPAN_MINUTES) * 100,
        "height_pct": (duration / _TOTAL_SPAN_MINUTES) * 100,
    }


SAMPLE_WEEK = [
    {
        "label": "Lun.",
        "date": "15/09",
        "events": [
            {
                "time": "09:00 – 10:05",
                "title": "Camille Thomas · Modelage bien-être",
                "color": "#7C8FF8",
                **_compute_block("09:00", "10:05"),
            },
            {
                "time": "11:30 – 12:30",
                "title": "Valérie · Soin découverte",
                "color": "#E07B39",
                **_compute_block("11:30", "12:30"),
            },
            {
                "time": "14:00 – 15:20",
                "title": "Valérie · Soin corps complet",
                "color": "#6BC0A5",
                **_compute_block("14:00", "15:20"),
            },
            {
                "time": "17:00 – 17:55",
                "title": "Jackie Vernhères · Modelage",
                "color": "#AF77E5",
                **_compute_block("17:00", "17:55"),
            },
        ],
    },
    {
        "label": "Mar.",
        "date": "16/09",
        "events": [
            {
                "time": "09:40 – 10:35",
                "title": "Laetitia · Kobido visage",
                "color": "#2CB7C6",
                **_compute_block("09:40", "10:35"),
            },
            {
                "time": "12:30 – 13:30",
                "title": "Valérie · Entreprise",
                "color": "#A7B0C0",
                **_compute_block("12:30", "13:30"),
            },
            {
                "time": "14:00 – 14:45",
                "title": "Prate Michelle · Massage",
                "color": "#F06FA7",
                **_compute_block("14:00", "14:45"),
            },
        ],
    },
    {
        "label": "Mer.",
        "date": "17/09",
        "events": [
            {
                "time": "09:00 – 14:00",
                "title": "Bloc formation interne",
                "color": "#D1D7E0",
                **_compute_block("09:00", "14:00"),
            }
        ],
    },
    {
        "label": "Jeu.",
        "date": "18/09",
        "events": [
            {
                "time": "09:15 – 09:45",
                "title": "Manon · Mise en beauté",
                "color": "#4AC07A",
                **_compute_block("09:15", "09:45"),
            },
            {
                "time": "11:15 – 12:15",
                "title": "Danny · Soin éclat intense",
                "color": "#5272FF",
                **_compute_block("11:15", "12:15"),
            },
            {
                "time": "14:15 – 15:20",
                "title": "Sarah B. · Modelage",
                "color": "#AF77E5",
                **_compute_block("14:15", "15:20"),
            },
            {
                "time": "17:00 – 17:45",
                "title": "Isabelle · Rehaussement de cils",
                "color": "#FFB347",
                **_compute_block("17:00", "17:45"),
            },
        ],
    },
    {
        "label": "Ven.",
        "date": "19/09",
        "events": [
            {
                "time": "09:00 – 09:35",
                "title": "Séverine · Pose vernis",
                "color": "#4AC07A",
                **_compute_block("09:00", "09:35"),
            },
            {
                "time": "11:00 – 12:00",
                "title": "Sabrina · Forfait duo",
                "color": "#E07B39",
                **_compute_block("11:00", "12:00"),
            },
            {
                "time": "18:00 – 18:25",
                "title": "Cousine Laure · Conseils",
                "color": "#F06FA7",
                **_compute_block("18:00", "18:25"),
            },
        ],
    },
    {
        "label": "Sam.",
        "date": "20/09",
        "events": [
            {
                "time": "09:00 – 10:30",
                "title": "Coaching maquillage",
                "color": "#7C8FF8",
                **_compute_block("09:00", "10:30"),
            },
            {
                "time": "14:00 – 15:30",
                "title": "Atelier collectif",
                "color": "#6BC0A5",
                **_compute_block("14:00", "15:30"),
            },
        ],
    },
    {
        "label": "Dim.",
        "date": "21/09",
        "events": [],
    },
]
