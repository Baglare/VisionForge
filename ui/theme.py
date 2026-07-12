"""VisionForge PySide6 arayüzü için ortak koyu tema."""


def application_stylesheet() -> str:
    """Uygulamanın sade, tekrar kullanılabilir Qt stilini döndürür."""
    return """
        QMainWindow, QWidget {
            background-color: #0B1017;
            color: #E6EDF3;
            font-family: "Segoe UI", Arial;
            font-size: 13px;
        }
        QFrame#TopBar, QFrame#NavPanel, QFrame#InfoCard,
        QFrame#PageCard, QFrame#SpellbookCard, QFrame#SystemRow,
        QFrame#CameraCard, QFrame#EnrollmentCard, QFrame#SettingCard,
        QFrame#NavFooter {
            background-color: #121A24;
            border: 1px solid #1E2B3A;
            border-radius: 10px;
        }
        QFrame#TopBar {
            background-color: #0E151E;
            border-radius: 0;
            border-width: 0 0 1px 0;
            border-color: #1B2836;
        }
        QFrame#NavPanel {
            background-color: #0E151E;
            border-color: #1B2836;
        }
        QFrame#NavFooter {
            background-color: #0B1119;
            border-color: #1B2836;
            border-radius: 7px;
        }
        QFrame#InfoCard {
            background-color: #121A24;
            border-color: #1B2836;
        }
        QFrame#CameraCard {
            background-color: #080C12;
            border-color: #263747;
            border-radius: 9px;
        }
        QLabel#BrandLabel {
            color: #2DD4BF;
            font-size: 18px;
            font-weight: 700;
        }
        QLabel#BrandSubtitle {
            color: #66778B;
            font-size: 10px;
        }
        QLabel#LivePageTitle {
            color: #E6EDF3;
            font-size: 17px;
            font-weight: 700;
        }
        QLabel#PageTitle {
            color: #E6EDF3;
            font-size: 22px;
            font-weight: 700;
        }
        QLabel#CardTitle, QLabel[role="muted"] {
            color: #91A0B3;
        }
        QLabel#CardTitle {
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        QLabel#NavGroupLabel {
            color: #66778B;
            font-size: 10px;
            font-weight: 700;
            padding: 2px 10px 4px 10px;
        }
        QLabel#ShortcutHint {
            color: #66778B;
            font-size: 10px;
            padding: 5px 7px;
        }
        QLabel[badge="true"] {
            background-color: #182330;
            border: 1px solid #263747;
            border-radius: 7px;
            padding: 5px 9px;
            font-size: 11px;
        }
        QLabel[badge="true"][state="neutral"] {
            color: #B4C0CE;
        }
        QLabel[badge="true"][state="rank"] {
            color: #D4A857;
            border-color: #57492D;
        }
        QLabel[badge="true"][state="verified"] {
            color: #2DD4BF;
            border-color: #245C58;
        }
        QLabel[badge="true"][state="warning"] {
            color: #F59E0B;
            border-color: #65461D;
        }
        QLabel[badge="true"][state="error"] {
            color: #EF4444;
            border-color: #652D34;
        }
        QLabel#CameraMeta {
            color: #91A0B3;
            background-color: #121A24;
            border: 1px solid #1E2B3A;
            border-radius: 6px;
            padding: 4px 7px;
            font-size: 10px;
        }
        QLabel#CameraMeta[state="verified"] {
            color: #2DD4BF;
        }
        QLabel#CameraMeta[state="error"] {
            color: #EF4444;
        }
        QLabel#MetricKey {
            color: #91A0B3;
            font-size: 11px;
        }
        QLabel#MetricValue {
            color: #E6EDF3;
            font-size: 12px;
            font-weight: 600;
        }
        QLabel#MetricValue[state="neutral"] {
            color: #B4C0CE;
        }
        QLabel#MetricValue[state="verified"] {
            color: #2DD4BF;
        }
        QLabel#MetricValue[state="warning"] {
            color: #F59E0B;
        }
        QLabel#MetricValue[state="error"] {
            color: #EF4444;
        }
        QLabel#MetricValue[state="rank"] {
            color: #D4A857;
        }
        QLabel#NotificationText {
            color: #B4C0CE;
            font-size: 11px;
        }
        QFrame#EnrollmentResultCard {
            background-color: #12231F;
            border: 1px solid #245C58;
            border-radius: 10px;
        }
        QLabel#EnrollmentStatus,
        QLabel#EnrollmentMessage {
            border-radius: 6px;
            padding: 5px 8px;
        }
        QLabel#EnrollmentStatus[state="neutral"],
        QLabel#EnrollmentMessage[state="neutral"] {
            color: #91A0B3;
            background-color: #182330;
        }
        QLabel#EnrollmentStatus[state="verified"] {
            color: #2DD4BF;
            background-color: #142B29;
        }
        QLabel#EnrollmentStatus[state="warning"],
        QLabel#EnrollmentMessage[state="warning"] {
            color: #F59E0B;
            background-color: #2B2114;
        }
        QLabel#EnrollmentMessage[state="error"] {
            color: #EF4444;
            background-color: #2A171C;
        }
        QLabel#SpellbookTitle {
            color: #D4A857;
            font-size: 28px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus[state="open"] {
            color: #2DD4BF;
            font-size: 16px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus[state="locked"] {
            color: #F59E0B;
            font-size: 16px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus[state="cover"] {
            color: #91A0B3;
            font-size: 16px;
            font-weight: 700;
        }
        QLabel#StatusValue[state="ok"], QLabel#TrialStep[state="complete"] {
            color: #2DD4BF;
            font-weight: 700;
        }
        QLabel#StatusValue[state="warning"] {
            color: #F59E0B;
            font-weight: 700;
        }
        QLabel#StatusValue[state="pending"], QLabel#TrialStep[state="pending"] {
            color: #91A0B3;
        }
        QLabel#TrialStep[state="active"] {
            color: #D4A857;
            font-weight: 700;
        }
        QPushButton {
            background-color: #182330;
            color: #E6EDF3;
            border: 1px solid #2A3A4D;
            border-radius: 7px;
            padding: 9px 12px;
        }
        QPushButton:hover {
            border-color: #2DD4BF;
            background-color: #1D2C3A;
        }
        QPushButton:pressed {
            background-color: #121A24;
        }
        QPushButton:disabled {
            color: #526174;
            border-color: #202C3A;
            background-color: #101821;
        }
        QPushButton[nav="true"] {
            text-align: left;
            border-color: transparent;
            background-color: transparent;
            padding: 10px 12px;
            color: #A8B5C4;
        }
        QPushButton[nav="true"]:hover {
            background-color: #16212D;
            border-color: transparent;
            color: #E6EDF3;
        }
        QPushButton[nav="true"]:pressed {
            background-color: #111B25;
        }
        QPushButton[nav="true"]:checked {
            color: #2DD4BF;
            background-color: #172B31;
            border-left: 3px solid #2DD4BF;
            font-weight: 700;
        }
        QPushButton[compact="true"] {
            text-align: center;
            padding: 7px 9px;
            font-size: 11px;
        }
        QCheckBox {
            spacing: 9px;
            padding: 7px 0;
        }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            border: 1px solid #526174;
            border-radius: 4px;
            background-color: #0B1017;
        }
        QCheckBox::indicator:checked {
            background-color: #2DD4BF;
            border-color: #2DD4BF;
        }
        QComboBox {
            background-color: #182330;
            border: 1px solid #2A3A4D;
            border-radius: 7px;
            padding: 8px 10px;
            min-width: 180px;
        }
        QLineEdit {
            background-color: #0E151E;
            color: #E6EDF3;
            border: 1px solid #2A3A4D;
            border-radius: 7px;
            padding: 8px 10px;
            selection-background-color: #245C58;
        }
        QLineEdit:focus {
            border-color: #2DD4BF;
        }
        QLineEdit:read-only {
            color: #91A0B3;
            background-color: #101821;
        }
        QComboBox QAbstractItemView {
            background-color: #182330;
            color: #E6EDF3;
            selection-background-color: #182F35;
            selection-color: #2DD4BF;
        }
        QProgressBar {
            background-color: #0B1017;
            border: 1px solid #2A3A4D;
            border-radius: 6px;
            text-align: center;
            min-height: 20px;
        }
        QProgressBar::chunk {
            background-color: #2DD4BF;
            border-radius: 5px;
        }
        QTabWidget::pane {
            background-color: #121A24;
            border: 1px solid #243244;
            border-radius: 8px;
        }
        QTabBar::tab {
            background-color: #121A24;
            color: #91A0B3;
            border: 1px solid #243244;
            padding: 9px 14px;
        }
        QTabBar::tab:selected {
            color: #2DD4BF;
            background-color: #182330;
        }
        QScrollArea, QStackedWidget {
            background-color: transparent;
            border: none;
        }
        QScrollBar:vertical {
            background: #0B1017;
            width: 10px;
            margin: 0;
        }
        QScrollBar::handle:vertical {
            background: #2A3A4D;
            border-radius: 5px;
            min-height: 24px;
        }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
            height: 0;
        }
        QToolTip {
            color: #E6EDF3;
            background-color: #182330;
            border: 1px solid #2DD4BF;
        }
    """
