"""Shared constants for the accounts application."""

PLANNER_HOURS = [f"{hour:02d}:00" for hour in range(8, 21)]
TOTAL_PLANNER_SPAN_MINUTES = 12 * 60  # 08:00 -> 20:00
PLANNER_COLOR_PALETTE = (
    "#7C8FF8",
    "#E07B39",
    "#6BC0A5",
    "#AF77E5",
    "#2CB7C6",
    "#F06FA7",
    "#4AC07A",
    "#5272FF",
    "#FFB347",
)

FALLBACK_WEEK = (
    (
        "Lun.",
        "15/09",
        (
            ("09:00", "10:05", "Modelage bien-être", "Camille Thomas", "#7C8FF8"),
            ("11:30", "12:30", "Soin découverte", "Valérie", "#E07B39"),
            ("14:00", "15:20", "Soin corps complet", "Valérie", "#6BC0A5"),
            ("17:00", "17:55", "Modelage", "Jackie Vernhères", "#AF77E5"),
        ),
    ),
    (
        "Mar.",
        "16/09",
        (
            ("09:40", "10:35", "Kobido visage", "Laetitia", "#2CB7C6"),
            ("12:30", "13:30", "Séance entreprise", "Valérie", "#A7B0C0"),
            ("14:00", "14:45", "Massage express", "Prate Michelle", "#F06FA7"),
        ),
    ),
    (
        "Mer.",
        "17/09",
        (
            ("09:00", "14:00", "Bloc formation interne", "Équipe interne", "#D1D7E0"),
        ),
    ),
    (
        "Jeu.",
        "18/09",
        (
            ("09:15", "09:45", "Mise en beauté", "Manon", "#4AC07A"),
            ("11:15", "12:15", "Soin éclat intense", "Danny", "#5272FF"),
            ("14:15", "15:20", "Modelage signature", "Sarah B.", "#AF77E5"),
            ("17:00", "17:45", "Rehaussement de cils", "Isabelle", "#FFB347"),
        ),
    ),
    (
        "Ven.",
        "19/09",
        (
            ("09:00", "09:35", "Pose vernis", "Séverine", "#4AC07A"),
            ("11:00", "12:00", "Forfait duo", "Sabrina", "#E07B39"),
            ("18:00", "18:25", "Conseils personnalisés", "Laure", "#F06FA7"),
        ),
    ),
    (
        "Sam.",
        "20/09",
        (
            ("09:00", "10:30", "Coaching maquillage", "Equipe collectif", "#7C8FF8"),
            ("14:00", "15:30", "Atelier collectif", "Equipe collectif", "#6BC0A5"),
        ),
    ),
    ("Dim.", "21/09", ()),
)
