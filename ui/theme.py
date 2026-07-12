"""VisionForge PySide6 arayüzü için ortak arcane-tech tasarım sistemi."""


def application_stylesheet() -> str:
    """Uygulamanın tekrar kullanılabilir koyu Qt stilini döndürür."""
    return """
        QMainWindow, QWidget {
            background-color: #080D13;
            color: #EDF3F7;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
            font-size: 13px;
        }
        QWidget:disabled {
            color: #526474;
        }
        QLabel {
            background-color: transparent;
        }
        QFrame#TopBar {
            background-color: #0C141D;
            border: 0;
            border-bottom: 1px solid #1B2A37;
            border-radius: 0;
        }
        QFrame#NavPanel {
            background-color: #0C141D;
            border: 1px solid #1A2936;
            border-radius: 12px;
        }
        QFrame#NavFooter {
            background-color: #0A1119;
            border: 1px solid #172532;
            border-radius: 9px;
        }
        QLabel#BrandLabel {
            color: #2DD4BF;
            font-size: 19px;
            font-weight: 700;
        }
        QLabel#BrandSubtitle {
            color: #6F8192;
            font-size: 10px;
        }
        QLabel#PageTitle {
            color: #EDF3F7;
            font-size: 24px;
            font-weight: 700;
        }
        QLabel#LivePageTitle {
            color: #EDF3F7;
            font-size: 18px;
            font-weight: 650;
        }
        QLabel[role="muted"], QLabel#CardDescription {
            color: #9AABBA;
            font-size: 12px;
        }
        QLabel#CardTitle {
            color: #9AABBA;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        QLabel#NavGroupLabel {
            color: #6F8192;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 0 12px 4px 12px;
        }
        QLabel#ShortcutHint {
            color: #6F8192;
            font-size: 10px;
            padding: 6px 8px;
        }

        QLabel[badge="true"] {
            background-color: #111B26;
            border: 1px solid #223442;
            border-radius: 9px;
            padding: 5px 10px;
            font-size: 11px;
        }
        QLabel[badge="true"][state="neutral"] { color: #9AABBA; }
        QLabel[badge="true"][state="rank"] {
            color: #E0B15A;
            border-color: #594A2F;
            background-color: #1B1A15;
        }
        QLabel[badge="true"][state="verified"] {
            color: #2DD4BF;
            border-color: #285B58;
            background-color: #10211F;
        }
        QLabel[badge="true"][state="warning"] {
            color: #F4B84A;
            border-color: #5D4827;
            background-color: #211B11;
        }
        QLabel[badge="true"][state="error"] {
            color: #EF646A;
            border-color: #623239;
            background-color: #231317;
        }

        QPushButton {
            min-height: 20px;
            background-color: #162432;
            color: #EDF3F7;
            border: 1px solid #294050;
            border-radius: 9px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #192A39;
            border-color: #3B5A6B;
        }
        QPushButton:pressed {
            background-color: #111B26;
            border-color: #2DD4BF;
        }
        QPushButton:focus {
            border: 1px solid #2DD4BF;
        }
        QPushButton:disabled {
            color: #526474;
            background-color: #0D151D;
            border-color: #1A2936;
        }
        QPushButton[buttonRole="primary"] {
            color: #061210;
            background-color: #2DD4BF;
            border-color: #2DD4BF;
            font-weight: 700;
        }
        QPushButton[buttonRole="primary"]:hover { background-color: #42DDC9; }
        QPushButton[buttonRole="primary"]:pressed { background-color: #21BCA9; }
        QPushButton[buttonRole="secondary"] { background-color: #111B26; }
        QPushButton[compact="true"] { padding: 6px 10px; font-size: 11px; }
        QPushButton[nav="true"] {
            min-height: 24px;
            text-align: left;
            color: #9AABBA;
            background-color: transparent;
            border: 1px solid transparent;
            border-left: 3px solid transparent;
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: 500;
        }
        QPushButton[nav="true"]:hover {
            color: #EDF3F7;
            background-color: #111B26;
            border-color: #1A2B38;
            border-left-color: transparent;
        }
        QPushButton[nav="true"]:pressed { background-color: #0E1922; }
        QPushButton[nav="true"]:checked {
            color: #2DD4BF;
            background-color: #14252B;
            border-color: #1B3439;
            border-left-color: #2DD4BF;
            font-weight: 700;
        }
        QPushButton[nav="true"]:focus { border-color: #2DD4BF; }

        QFrame#InfoCard, QFrame#PageCard, QFrame#EnrollmentCard,
        QFrame#SettingCard, QFrame#SectionCard, QFrame#DebugGroupCard,
        QFrame#ArchiveMetaCard, QFrame#TrialStepCard, QFrame#TrialSummaryCard,
        QFrame#SpellbookNavCard {
            background-color: #111B26;
            border: 1px solid #1C2C39;
            border-radius: 12px;
        }
        QFrame#InfoCard:hover, QFrame#SettingCard:hover {
            border-color: #29404E;
        }
        QFrame#CameraCard {
            background-color: #05090E;
            border: 1px solid #243846;
            border-radius: 12px;
        }
        QFrame#EnrollmentResultCard {
            background-color: #10211F;
            border: 1px solid #285B58;
            border-radius: 12px;
        }
        QFrame#SectionCard QLabel, QFrame#DebugGroupCard QLabel,
        QFrame#ArchiveMetaCard QLabel, QFrame#TrialStepCard QLabel,
        QFrame#TrialSummaryCard QLabel, QFrame#SpellbookCard QLabel,
        QFrame#SpellbookNavCard QLabel, QFrame#SystemRow QLabel {
            background: transparent;
        }

        QLabel#CameraMeta {
            color: #9AABBA;
            background-color: #111B26;
            border: 1px solid #1C2C39;
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 10px;
        }
        QLabel#CameraMeta[state="verified"] { color: #2DD4BF; border-color: #285B58; }
        QLabel#CameraMeta[state="error"] { color: #EF646A; border-color: #623239; }
        QLabel#MetricKey { color: #6F8192; font-size: 11px; }
        QLabel#MetricValue {
            color: #EDF3F7;
            font-size: 12px;
            font-weight: 600;
        }
        QLabel#MetricValue[state="neutral"] { color: #9AABBA; }
        QLabel#MetricValue[state="verified"] { color: #2DD4BF; }
        QLabel#MetricValue[state="warning"] { color: #F4B84A; }
        QLabel#MetricValue[state="error"] { color: #EF646A; }
        QLabel#MetricValue[state="rank"] { color: #E0B15A; }
        QLabel#NotificationText { color: #9AABBA; font-size: 11px; }

        QFrame#SpellbookCard {
            background-color: #111B26;
            border: 1px solid #29404E;
            border-radius: 14px;
        }
        QFrame#SpellbookCard[state="cover"] { border-color: #344A58; }
        QFrame#SpellbookCard[state="open"] { border-color: #2A6962; background-color: #0E1D20; }
        QFrame#SpellbookCard[state="locked"] { border-color: #4B4538; background-color: #15191E; }
        QLabel#SpellbookTitle {
            color: #E0B15A;
            font-size: 34px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus {
            border-radius: 9px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus[state="open"] { color: #2DD4BF; background-color: #12322F; }
        QLabel#SpellbookStatus[state="locked"] { color: #F4B84A; background-color: #2A2114; }
        QLabel#SpellbookStatus[state="cover"] { color: #9AABBA; background-color: #162432; }
        QLabel#SpellbookCoverHint {
            color: #9AABBA;
            font-size: 14px;
            line-height: 1.4;
        }
        QLabel#ArchiveMetaValue { color: #EDF3F7; font-size: 15px; font-weight: 650; }
        QLabel#ArchiveRankValue { color: #E0B15A; font-size: 15px; font-weight: 700; }
        QLabel#ArchiveBodyText { color: #C5D0D8; font-size: 13px; }
        QLabel#SpellbookPageIndicator {
            color: #EDF3F7;
            font-size: 20px;
            font-weight: 700;
        }
        QLabel#SpellbookAccessSummary {
            color: #9AABBA;
            background-color: #0D1720;
            border: 1px solid #1B2D3A;
            border-radius: 9px;
            padding: 10px;
        }
        QLabel#SpellbookNavItem {
            color: #6F8192;
            border-left: 2px solid #223442;
            padding: 8px 10px;
            font-weight: 600;
        }
        QLabel#SpellbookNavItem[state="open"] { color: #9AABBA; }
        QLabel#SpellbookNavItem[state="locked"] { color: #566879; }
        QLabel#SpellbookNavItem[state="active"] {
            color: #2DD4BF;
            background-color: #14252B;
            border-left-color: #2DD4BF;
        }

        QLabel#TrialStepIndex {
            min-width: 18px;
            color: #9AABBA;
            background-color: #162432;
            border: 1px solid #29404E;
            border-radius: 9px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 700;
        }
        QLabel#TrialStepName { color: #EDF3F7; font-size: 17px; font-weight: 700; }
        QLabel#TrialStepTrigger { color: #9AABBA; font-size: 12px; }
        QFrame#TrialStepCard[state="complete"] { background-color: #0F211F; border-color: #285B58; }
        QFrame#TrialStepCard[state="active"] { background-color: #211C13; border-color: #806431; }
        QFrame#TrialStepCard[state="locked"] { background-color: #0D151D; border-color: #253442; }
        QLabel#TrialStepStatus, QLabel#TrialSummaryStatus,
        QLabel#SystemGroupStatus, QLabel#EnrollmentStatus, QLabel#EnrollmentMessage {
            border-radius: 8px;
            padding: 4px 9px;
            font-size: 10px;
            font-weight: 700;
        }
        QLabel#TrialStepStatus[state="complete"], QLabel#TrialSummaryStatus[state="verified"],
        QLabel#SystemGroupStatus[state="verified"], QLabel#EnrollmentStatus[state="verified"] {
            color: #2DD4BF; background-color: #12322F;
        }
        QLabel#TrialStepStatus[state="active"], QLabel#TrialSummaryStatus[state="warning"],
        QLabel#SystemGroupStatus[state="warning"], QLabel#EnrollmentStatus[state="warning"],
        QLabel#EnrollmentMessage[state="warning"] {
            color: #F4B84A; background-color: #2A2114;
        }
        QLabel#TrialStepStatus[state="locked"] { color: #F4B84A; background-color: #211A11; }
        QLabel#TrialStepStatus[state="pending"], QLabel#TrialSummaryStatus[state="neutral"],
        QLabel#SystemGroupStatus[state="neutral"], QLabel#EnrollmentStatus[state="neutral"],
        QLabel#EnrollmentMessage[state="neutral"] {
            color: #9AABBA; background-color: #162432;
        }
        QLabel#EnrollmentMessage[state="error"] { color: #EF646A; background-color: #28171B; }

        QFrame#SystemRow {
            background-color: #0D1720;
            border: 1px solid #182A37;
            border-radius: 9px;
        }
        QLabel#SystemItemName { color: #EDF3F7; font-size: 12px; font-weight: 650; }
        QLabel#SystemHint { color: #6F8192; font-size: 11px; }
        QLabel#StatusValue { font-size: 11px; font-weight: 700; }
        QLabel#StatusValue[state="ok"] { color: #2DD4BF; }
        QLabel#StatusValue[state="warning"] { color: #F4B84A; }
        QLabel#StatusValue[state="pending"] { color: #9AABBA; }

        QLabel#DebugKey { color: #6F8192; font-size: 11px; }
        QLabel#DebugValue {
            color: #D8E3EA;
            background-color: #0D1720;
            border: 1px solid #172834;
            border-radius: 7px;
            padding: 5px 8px;
            font-family: "Cascadia Mono", "Consolas", monospace;
            font-size: 10px;
        }

        QCheckBox#SettingOption {
            color: #D8E3EA;
            background-color: #0D1720;
            border: 1px solid #182A37;
            border-radius: 9px;
            padding: 10px 12px;
            spacing: 10px;
        }
        QCheckBox#SettingOption:hover { border-color: #294757; }
        QCheckBox { spacing: 10px; }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            background-color: #080D13;
            border: 1px solid #4A5E6D;
            border-radius: 5px;
        }
        QCheckBox::indicator:hover { border-color: #2DD4BF; }
        QCheckBox::indicator:checked { background-color: #2DD4BF; border-color: #2DD4BF; }
        QCheckBox:focus { color: #2DD4BF; }

        QLineEdit, QComboBox {
            min-height: 22px;
            color: #EDF3F7;
            background-color: #0D1720;
            border: 1px solid #29404E;
            border-radius: 9px;
            padding: 7px 10px;
            selection-background-color: #285B58;
        }
        QLineEdit:hover, QComboBox:hover { border-color: #3B5968; }
        QLineEdit:focus, QComboBox:focus { border-color: #2DD4BF; }
        QLineEdit:read-only { color: #9AABBA; background-color: #0A121A; }
        QComboBox { min-width: 176px; }
        QComboBox QAbstractItemView {
            color: #EDF3F7;
            background-color: #162432;
            border: 1px solid #29404E;
            selection-color: #2DD4BF;
            selection-background-color: #142B30;
        }
        QProgressBar {
            min-height: 20px;
            color: #EDF3F7;
            background-color: #0A121A;
            border: 1px solid #243947;
            border-radius: 8px;
            text-align: center;
            font-size: 10px;
            font-weight: 600;
        }
        QProgressBar::chunk { background-color: #2DD4BF; border-radius: 7px; }

        QTabWidget::pane {
            background-color: #0C141D;
            border: 1px solid #1C2C39;
            border-radius: 11px;
            top: -1px;
        }
        QTabBar::tab {
            color: #9AABBA;
            background-color: #0C141D;
            border: 1px solid #1C2C39;
            border-bottom: 0;
            padding: 9px 16px;
        }
        QTabBar::tab:first { border-top-left-radius: 9px; }
        QTabBar::tab:last { border-top-right-radius: 9px; }
        QTabBar::tab:hover { color: #EDF3F7; background-color: #111B26; }
        QTabBar::tab:selected { color: #2DD4BF; background-color: #162432; }
        QTabBar::tab:focus { border-color: #2DD4BF; }

        QScrollArea, QStackedWidget { background-color: transparent; border: none; }
        QScrollBar:vertical {
            width: 10px;
            background: #080D13;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            min-height: 28px;
            background: #29404E;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover { background: #385666; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QToolTip {
            color: #EDF3F7;
            background-color: #192A39;
            border: 1px solid #3A5968;
            padding: 6px;
        }
    """
