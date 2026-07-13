"""VisionForge PySide6 arayüzü için ortak gece-indigo tasarım sistemi."""


def application_stylesheet() -> str:
    """Uygulamanın tekrar kullanılabilir koyu Qt stilini döndürür."""
    return """
        QMainWindow, QWidget {
            background-color: #010117;
            color: #F7E5FD;
            font-family: "Segoe UI Variable", "Segoe UI", Arial;
            font-size: 13px;
        }
        QWidget:disabled {
            color: #817A98;
        }
        QLabel {
            background-color: transparent;
        }
        QFrame#TopBar {
            background-color: #050129;
            border: 0;
            border-bottom: 1px solid #26125D;
            border-radius: 0;
        }
        QFrame#NavPanel {
            background-color: #050129;
            border: 1px solid #241157;
            border-radius: 12px;
        }
        QFrame#NavFooter {
            background-color: #080333;
            border: 1px solid #21104E;
            border-radius: 9px;
        }
        QLabel#BrandLabel {
            color: #B37AF8;
            font-size: 19px;
            font-weight: 700;
        }
        QLabel#BrandSubtitle {
            color: #8F88A8;
            font-size: 10px;
        }
        QLabel#PageTitle {
            color: #F7E5FD;
            font-size: 24px;
            font-weight: 700;
        }
        QLabel#LivePageTitle {
            color: #F7E5FD;
            font-size: 18px;
            font-weight: 650;
        }
        QLabel[role="muted"], QLabel#CardDescription {
            color: #B4ACC4;
            font-size: 12px;
        }
        QLabel#CardTitle {
            color: #AAA2BB;
            font-size: 11px;
            font-weight: 700;
            letter-spacing: 1px;
        }
        QLabel#NavGroupLabel {
            color: #817A98;
            font-size: 10px;
            font-weight: 700;
            letter-spacing: 1px;
            padding: 0 12px 4px 12px;
        }
        QLabel#ShortcutHint {
            color: #8F88A8;
            font-size: 10px;
            padding: 6px 8px;
        }

        QLabel[badge="true"] {
            background-color: #0D0641;
            border: 1px solid #2C1766;
            border-radius: 9px;
            padding: 5px 10px;
            font-size: 11px;
        }
        QLabel[badge="true"][state="neutral"] { color: #B4ACC4; }
        QLabel[badge="true"][state="rank"] {
            color: #DAACFB;
            border-color: #45247F;
            background-color: #10063C;
        }
        QLabel[badge="true"][state="verified"] {
            color: #E5C4FC;
            border-color: #5B2DB5;
            background-color: #130846;
        }
        QLabel[badge="true"][state="warning"] {
            color: #F4BF62;
            border-color: #6B5128;
            background-color: #251B12;
        }
        QLabel[badge="true"][state="error"] {
            color: #F27B82;
            border-color: #70333E;
            background-color: #28131B;
        }

        QPushButton {
            min-height: 20px;
            background-color: #12084B;
            color: #F7E5FD;
            border: 1px solid #382078;
            border-radius: 9px;
            padding: 8px 14px;
            font-weight: 600;
        }
        QPushButton:hover {
            background-color: #1B0D68;
            border-color: #6540A3;
        }
        QPushButton:pressed {
            background-color: #110377;
            border-color: #8F53F8;
        }
        QPushButton:focus {
            border: 1px solid #8F53F8;
        }
        QPushButton:disabled {
            color: #817A98;
            background-color: #080329;
            border-color: #211044;
        }
        QPushButton[buttonRole="primary"] {
            color: #F7E5FD;
            background-color: #5525D0;
            border-color: #6934F5;
            font-weight: 700;
        }
        QPushButton[buttonRole="primary"]:hover {
            background-color: #6934F5;
            border-color: #8F53F8;
        }
        QPushButton[buttonRole="primary"]:pressed {
            background-color: #471BD7;
            border-color: #6934F5;
        }
        QPushButton[buttonRole="secondary"] { background-color: #0D0641; }
        QPushButton[compact="true"] { padding: 6px 10px; font-size: 11px; }
        QPushButton[nav="true"] {
            min-height: 24px;
            text-align: left;
            color: #AAA2BB;
            background-color: transparent;
            border: 1px solid transparent;
            border-left: 3px solid transparent;
            border-radius: 8px;
            padding: 8px 12px;
            font-weight: 500;
        }
        QPushButton[nav="true"]:hover {
            color: #F7E5FD;
            background-color: #0D0641;
            border-color: #2A155E;
            border-left-color: transparent;
        }
        QPushButton[nav="true"]:pressed { background-color: #110653; }
        QPushButton[nav="true"]:checked {
            color: #E5C4FC;
            background-color: #120743;
            border-color: #32176C;
            border-left-color: #7D4BE0;
            font-weight: 700;
        }
        QPushButton[nav="true"]:focus { border-color: #8F53F8; }

        QFrame#InfoCard, QFrame#PageCard, QFrame#EnrollmentCard,
        QFrame#SettingCard, QFrame#SectionCard, QFrame#DebugGroupCard,
        QFrame#ArchiveMetaCard, QFrame#TrialStepCard, QFrame#TrialSummaryCard,
        QFrame#SpellbookNavCard {
            background-color: #090434;
            border: 1px solid #28145E;
            border-radius: 12px;
        }
        QFrame#InfoCard:hover, QFrame#SettingCard:hover {
            border-color: #432584;
        }
        QFrame#InfoCard[cardRole="activeSpell"] {
            background-color: #0A0435;
            border-color: #48278D;
        }
        QFrame#InfoCard[cardRole="activeSpell"] QLabel#CardTitle {
            color: #B37AF8;
        }
        QFrame#CameraCard {
            background-color: #010117;
            border: 1px solid #321A7B;
            border-radius: 12px;
        }
        QFrame#EnrollmentResultCard {
            background-color: #071D17;
            border: 1px solid #347555;
            border-radius: 12px;
        }
        QFrame#SectionCard QLabel, QFrame#DebugGroupCard QLabel,
        QFrame#ArchiveMetaCard QLabel, QFrame#TrialStepCard QLabel,
        QFrame#TrialSummaryCard QLabel, QFrame#SpellbookCard QLabel,
        QFrame#SpellbookNavCard QLabel, QFrame#SystemRow QLabel {
            background: transparent;
        }

        QLabel#CameraMeta {
            color: #B4ACC4;
            background-color: #0D0641;
            border: 1px solid #2A1762;
            border-radius: 8px;
            padding: 4px 8px;
            font-size: 10px;
        }
        QLabel#CameraMeta[state="verified"] { color: #78D6A2; border-color: #347555; }
        QLabel#CameraMeta[state="error"] { color: #F27B82; border-color: #70333E; }
        QLabel#MetricKey { color: #8F88A8; font-size: 11px; }
        QLabel#MetricValue {
            color: #F7E5FD;
            font-size: 12px;
            font-weight: 600;
        }
        QLabel#MetricValue[state="neutral"] { color: #B4ACC4; }
        QLabel#MetricValue[state="verified"] { color: #DAACFB; }
        QLabel#MetricValue[state="warning"] { color: #F4BF62; }
        QLabel#MetricValue[state="error"] { color: #F27B82; }
        QLabel#MetricValue[state="rank"] { color: #DAACFB; }
        QLabel#NotificationText { color: #B4ACC4; font-size: 11px; }

        QFrame#SpellbookCard {
            background-color: #0A0438;
            border: 1px solid #382078;
            border-radius: 14px;
        }
        QFrame#SpellbookCard[state="cover"] { border-color: #47258D; }
        QFrame#SpellbookCard[state="open"] { border-color: #4E279B; background-color: #0A0430; }
        QFrame#SpellbookCard[state="locked"] { border-color: #2B1A58; background-color: #08042C; }
        QLabel#SpellbookTitle {
            color: #DAACFB;
            font-size: 34px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus {
            border-radius: 9px;
            padding: 5px 10px;
            font-size: 12px;
            font-weight: 700;
        }
        QLabel#SpellbookStatus[state="open"] { color: #E5C4FC; background-color: #271067; }
        QLabel#SpellbookStatus[state="locked"] { color: #958CAB; background-color: #10083A; }
        QLabel#SpellbookStatus[state="cover"] { color: #B4ACC4; background-color: #12084B; }
        QLabel#SpellbookCoverHint {
            color: #B4ACC4;
            font-size: 14px;
            line-height: 1.4;
        }
        QLabel#ArchiveMetaValue { color: #F7E5FD; font-size: 15px; font-weight: 650; }
        QLabel#ArchiveRankValue { color: #DAACFB; font-size: 15px; font-weight: 700; }
        QLabel#ArchiveBodyText { color: #D1C8DD; font-size: 13px; }
        QLabel#SpellbookPageIndicator {
            color: #F7E5FD;
            font-size: 20px;
            font-weight: 700;
        }
        QLabel#SpellbookAccessSummary {
            color: #B4ACC4;
            background-color: #080331;
            border: 1px solid #251257;
            border-radius: 9px;
            padding: 10px;
        }
        QLabel#SpellbookNavItem {
            color: #8F88A8;
            border-left: 2px solid #2A1762;
            padding: 8px 10px;
            font-weight: 600;
        }
        QLabel#SpellbookNavItem[state="open"] { color: #BFAFD0; }
        QLabel#SpellbookNavItem[state="locked"] { color: #756E8D; }
        QLabel#SpellbookNavItem[state="active"] {
            color: #E5C4FC;
            background-color: #16084C;
            border-left-color: #7D4BE0;
        }

        QLabel#TrialStepIndex {
            min-width: 18px;
            color: #B4ACC4;
            background-color: #12084B;
            border: 1px solid #382078;
            border-radius: 9px;
            padding: 3px 8px;
            font-size: 11px;
            font-weight: 700;
        }
        QLabel#TrialStepName { color: #F7E5FD; font-size: 17px; font-weight: 700; }
        QLabel#TrialStepTrigger { color: #B4ACC4; font-size: 12px; }
        QFrame#TrialStepCard[state="complete"] { background-color: #071D17; border-color: #347555; }
        QFrame#TrialStepCard[state="active"] { background-color: #0D053B; border-color: #6D3BD7; }
        QFrame#TrialStepCard[state="locked"] { background-color: #17101C; border-color: #6B5128; }
        QLabel#TrialStepStatus, QLabel#TrialSummaryStatus,
        QLabel#SystemGroupStatus, QLabel#EnrollmentStatus, QLabel#EnrollmentMessage {
            border-radius: 8px;
            padding: 4px 9px;
            font-size: 10px;
            font-weight: 700;
        }
        QLabel#TrialStepStatus[state="complete"], QLabel#TrialSummaryStatus[state="verified"],
        QLabel#SystemGroupStatus[state="verified"], QLabel#EnrollmentStatus[state="verified"] {
            color: #78D6A2; background-color: #0B2B20;
        }
        QLabel#TrialStepStatus[state="active"], QLabel#TrialSummaryStatus[state="warning"] {
            color: #E5C4FC; background-color: #271067;
        }
        QLabel#EnrollmentStatus[state="warning"] {
            color: #E5C4FC; background-color: #271067;
        }
        QLabel#SystemGroupStatus[state="warning"], QLabel#EnrollmentMessage[state="warning"] {
            color: #F4BF62; background-color: #2B2013;
        }
        QLabel#TrialStepStatus[state="locked"] { color: #F4BF62; background-color: #2B2013; }
        QLabel#TrialStepStatus[state="pending"], QLabel#TrialSummaryStatus[state="neutral"],
        QLabel#SystemGroupStatus[state="neutral"], QLabel#EnrollmentStatus[state="neutral"],
        QLabel#EnrollmentMessage[state="neutral"] {
            color: #AAA2BB; background-color: #12084B;
        }
        QLabel#EnrollmentMessage[state="error"] { color: #F27B82; background-color: #30151E; }

        QFrame#SystemRow {
            background-color: #080331;
            border: 1px solid #21104E;
            border-radius: 9px;
        }
        QLabel#SystemItemName { color: #F7E5FD; font-size: 12px; font-weight: 650; }
        QLabel#SystemHint { color: #8F88A8; font-size: 11px; }
        QLabel#StatusValue { font-size: 11px; font-weight: 700; }
        QLabel#StatusValue[state="ok"] { color: #78D6A2; }
        QLabel#StatusValue[state="warning"] { color: #F4BF62; }
        QLabel#StatusValue[state="pending"] { color: #AAA2BB; }

        QLabel#DebugKey { color: #8F88A8; font-size: 11px; }
        QLabel#DebugValue {
            color: #DDD5E8;
            background-color: #080331;
            border: 1px solid #251257;
            border-radius: 7px;
            padding: 5px 8px;
            font-family: "Cascadia Mono", "Consolas", monospace;
            font-size: 10px;
        }

        QCheckBox#SettingOption {
            color: #DDD5E8;
            background-color: #080331;
            border: 1px solid #251257;
            border-radius: 9px;
            padding: 10px 12px;
            spacing: 10px;
        }
        QCheckBox#SettingOption:hover { border-color: #503092; }
        QCheckBox#SettingOption:focus { border-color: #8F53F8; }
        QCheckBox { spacing: 10px; }
        QCheckBox::indicator {
            width: 18px;
            height: 18px;
            background-color: #010117;
            border: 1px solid #655D79;
            border-radius: 5px;
        }
        QCheckBox::indicator:hover { border-color: #8F53F8; }
        QCheckBox::indicator:checked { background-color: #5525D0; border-color: #7D4BE0; }
        QCheckBox::indicator:disabled { background-color: #080329; border-color: #30294A; }
        QCheckBox:focus { color: #DAACFB; }

        QLineEdit, QComboBox {
            min-height: 22px;
            color: #F7E5FD;
            background-color: #080331;
            border: 1px solid #382078;
            border-radius: 9px;
            padding: 7px 10px;
            selection-color: #F7E5FD;
            selection-background-color: #471BD7;
        }
        QLineEdit:hover, QComboBox:hover { border-color: #6540A3; }
        QLineEdit:focus, QComboBox:focus { border-color: #8F53F8; }
        QLineEdit:read-only { color: #AAA2BB; background-color: #050126; }
        QLineEdit:disabled, QComboBox:disabled {
            color: #817A98;
            background-color: #050126;
            border-color: #211044;
        }
        QComboBox { min-width: 176px; }
        QComboBox QAbstractItemView {
            color: #F7E5FD;
            background-color: #100747;
            border: 1px solid #432584;
            selection-color: #F7E5FD;
            selection-background-color: #471BD7;
        }
        QProgressBar {
            min-height: 20px;
            color: #F7E5FD;
            background-color: #050126;
            border: 1px solid #321A6D;
            border-radius: 8px;
            text-align: center;
            font-size: 10px;
            font-weight: 600;
        }
        QProgressBar::chunk {
            background: qlineargradient(x1:0, y1:0, x2:1, y2:0, stop:0 #5525D0, stop:1 #7540DF);
            border-radius: 7px;
        }

        QTabWidget::pane {
            background-color: #050129;
            border: 1px solid #28145E;
            border-radius: 11px;
            top: -1px;
        }
        QTabBar::tab {
            color: #AAA2BB;
            background-color: #050129;
            border: 1px solid #28145E;
            border-bottom: 0;
            padding: 9px 16px;
        }
        QTabBar::tab:first { border-top-left-radius: 9px; }
        QTabBar::tab:last { border-top-right-radius: 9px; }
        QTabBar::tab:hover { color: #F7E5FD; background-color: #0D0641; }
        QTabBar::tab:selected { color: #E5C4FC; background-color: #16084C; }
        QTabBar::tab:focus { border-color: #8F53F8; }

        QScrollArea, QStackedWidget { background-color: transparent; border: none; }
        QScrollBar:vertical {
            width: 10px;
            background: #010117;
            margin: 2px;
        }
        QScrollBar::handle:vertical {
            min-height: 28px;
            background: #382078;
            border-radius: 4px;
        }
        QScrollBar::handle:vertical:hover { background: #5A35A0; }
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
        QToolTip {
            color: #F7E5FD;
            background-color: #16095A;
            border: 1px solid #6540A3;
            padding: 6px;
        }
    """
