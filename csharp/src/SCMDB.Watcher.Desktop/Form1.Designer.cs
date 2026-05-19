namespace SCMDB.Watcher.Desktop;

partial class Form1
{
    /// <summary>
    ///  Required designer variable.
    /// </summary>
    private System.ComponentModel.IContainer components = null;

    /// <summary>
    ///  Clean up any resources being used.
    /// </summary>
    /// <param name="disposing">true if managed resources should be disposed; otherwise, false.</param>
    protected override void Dispose(bool disposing)
    {
        if (disposing && (components != null))
        {
            components.Dispose();
        }
        base.Dispose(disposing);
    }

    #region Windows Form Designer generated code

    /// <summary>
    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    /// </summary>
    private Label lblTitle;
    private Label lblStatus;
    private Label lblGameDir;
    private Label lblChannel;
    private Label lblLanguage;
    private Label lblLogPath;
    private TextBox txtSummary;
    private TextBox txtGameDir;
    private TextBox txtLogPath;
    private ComboBox cmbChannel;
    private ComboBox cmbLanguage;
    private Button btnStart;
    private Button btnStop;
    private Button btnReload;
    private Button btnSaveConfig;
    private Button btnBrowseGameDir;
    private Button btnBrowseLogPath;
    private Button btnImport;
    private Button btnOpenRuntime;

    /// <summary>
    ///  Required method for Designer support - do not modify
    ///  the contents of this method with the code editor.
    /// </summary>
    private void InitializeComponent()
    {
        components = new System.ComponentModel.Container();
        lblTitle = new Label();
        lblStatus = new Label();
        lblGameDir = new Label();
        lblChannel = new Label();
        lblLanguage = new Label();
        lblLogPath = new Label();
        txtSummary = new TextBox();
        txtGameDir = new TextBox();
        txtLogPath = new TextBox();
        cmbChannel = new ComboBox();
        cmbLanguage = new ComboBox();
        btnStart = new Button();
        btnStop = new Button();
        btnReload = new Button();
        btnSaveConfig = new Button();
        btnBrowseGameDir = new Button();
        btnBrowseLogPath = new Button();
        btnImport = new Button();
        btnOpenRuntime = new Button();
        SuspendLayout();
        //
        // lblTitle
        //
        lblTitle.AutoSize = true;
        lblTitle.Font = new Font("Segoe UI", 14F, FontStyle.Bold);
        lblTitle.Location = new Point(18, 16);
        lblTitle.Name = "lblTitle";
        lblTitle.Size = new Size(244, 25);
        lblTitle.TabIndex = 0;
        lblTitle.Text = "SCMDB Watcher Migration";
        //
        // lblStatus
        //
        lblStatus.AutoSize = true;
        lblStatus.Location = new Point(24, 56);
        lblStatus.Name = "lblStatus";
        lblStatus.Size = new Size(39, 15);
        lblStatus.TabIndex = 1;
        lblStatus.Text = "Status";
        //
        // lblGameDir
        //
        lblGameDir.AutoSize = true;
        lblGameDir.Location = new Point(24, 98);
        lblGameDir.Name = "lblGameDir";
        lblGameDir.Size = new Size(54, 15);
        lblGameDir.TabIndex = 2;
        lblGameDir.Text = "Game dir";
        //
        // lblChannel
        //
        lblChannel.AutoSize = true;
        lblChannel.Location = new Point(24, 134);
        lblChannel.Name = "lblChannel";
        lblChannel.Size = new Size(49, 15);
        lblChannel.TabIndex = 5;
        lblChannel.Text = "Channel";
        //
        // lblLanguage
        //
        lblLanguage.AutoSize = true;
        lblLanguage.Location = new Point(278, 134);
        lblLanguage.Name = "lblLanguage";
        lblLanguage.Size = new Size(59, 15);
        lblLanguage.TabIndex = 7;
        lblLanguage.Text = "Language";
        //
        // lblLogPath
        //
        lblLogPath.AutoSize = true;
        lblLogPath.Location = new Point(24, 170);
        lblLogPath.Name = "lblLogPath";
        lblLogPath.Size = new Size(51, 15);
        lblLogPath.TabIndex = 9;
        lblLogPath.Text = "Log path";
        //
        // txtSummary
        //
        txtSummary.Location = new Point(22, 255);
        txtSummary.Multiline = true;
        txtSummary.Name = "txtSummary";
        txtSummary.ReadOnly = true;
        txtSummary.ScrollBars = ScrollBars.Vertical;
        txtSummary.Size = new Size(744, 221);
        txtSummary.TabIndex = 16;
        //
        // txtGameDir
        //
        txtGameDir.Location = new Point(92, 95);
        txtGameDir.Name = "txtGameDir";
        txtGameDir.Size = new Size(580, 23);
        txtGameDir.TabIndex = 3;
        //
        // txtLogPath
        //
        txtLogPath.Location = new Point(92, 167);
        txtLogPath.Name = "txtLogPath";
        txtLogPath.Size = new Size(580, 23);
        txtLogPath.TabIndex = 10;
        //
        // cmbChannel
        //
        cmbChannel.DropDownStyle = ComboBoxStyle.DropDownList;
        cmbChannel.FormattingEnabled = true;
        cmbChannel.Items.AddRange(new object[] { "LIVE", "HOTFIX" });
        cmbChannel.Location = new Point(92, 131);
        cmbChannel.Name = "cmbChannel";
        cmbChannel.Size = new Size(140, 23);
        cmbChannel.TabIndex = 6;
        //
        // cmbLanguage
        //
        cmbLanguage.DropDownStyle = ComboBoxStyle.DropDownList;
        cmbLanguage.FormattingEnabled = true;
        cmbLanguage.Items.AddRange(new object[] { "es", "en" });
        cmbLanguage.Location = new Point(351, 131);
        cmbLanguage.Name = "cmbLanguage";
        cmbLanguage.Size = new Size(140, 23);
        cmbLanguage.TabIndex = 8;
        //
        // btnStart
        //
        btnStart.Location = new Point(494, 51);
        btnStart.Name = "btnStart";
        btnStart.Size = new Size(84, 29);
        btnStart.TabIndex = 2;
        btnStart.Text = "Start";
        btnStart.UseVisualStyleBackColor = true;
        //
        // btnStop
        //
        btnStop.Location = new Point(588, 51);
        btnStop.Name = "btnStop";
        btnStop.Size = new Size(84, 29);
        btnStop.TabIndex = 3;
        btnStop.Text = "Stop";
        btnStop.UseVisualStyleBackColor = true;
        //
        // btnReload
        //
        btnReload.Location = new Point(682, 51);
        btnReload.Name = "btnReload";
        btnReload.Size = new Size(84, 29);
        btnReload.TabIndex = 4;
        btnReload.Text = "Reload";
        btnReload.UseVisualStyleBackColor = true;
        //
        // btnSaveConfig
        //
        btnSaveConfig.Location = new Point(588, 208);
        btnSaveConfig.Name = "btnSaveConfig";
        btnSaveConfig.Size = new Size(84, 29);
        btnSaveConfig.TabIndex = 13;
        btnSaveConfig.Text = "Save";
        btnSaveConfig.UseVisualStyleBackColor = true;
        //
        // btnBrowseGameDir
        //
        btnBrowseGameDir.Location = new Point(682, 93);
        btnBrowseGameDir.Name = "btnBrowseGameDir";
        btnBrowseGameDir.Size = new Size(84, 27);
        btnBrowseGameDir.TabIndex = 4;
        btnBrowseGameDir.Text = "Browse...";
        btnBrowseGameDir.UseVisualStyleBackColor = true;
        //
        // btnBrowseLogPath
        //
        btnBrowseLogPath.Location = new Point(682, 165);
        btnBrowseLogPath.Name = "btnBrowseLogPath";
        btnBrowseLogPath.Size = new Size(84, 27);
        btnBrowseLogPath.TabIndex = 11;
        btnBrowseLogPath.Text = "Browse...";
        btnBrowseLogPath.UseVisualStyleBackColor = true;
        //
        // btnImport
        //
        btnImport.Location = new Point(682, 208);
        btnImport.Name = "btnImport";
        btnImport.Size = new Size(84, 29);
        btnImport.TabIndex = 14;
        btnImport.Text = "Import";
        btnImport.UseVisualStyleBackColor = true;
        //
        // btnOpenRuntime
        //
        btnOpenRuntime.Location = new Point(22, 208);
        btnOpenRuntime.Name = "btnOpenRuntime";
        btnOpenRuntime.Size = new Size(124, 29);
        btnOpenRuntime.TabIndex = 12;
        btnOpenRuntime.Text = "Open runtime";
        btnOpenRuntime.UseVisualStyleBackColor = true;
        AutoScaleMode = AutoScaleMode.Font;
        ClientSize = new Size(784, 491);
        Controls.Add(btnOpenRuntime);
        Controls.Add(btnImport);
        Controls.Add(btnBrowseLogPath);
        Controls.Add(btnBrowseGameDir);
        Controls.Add(btnSaveConfig);
        Controls.Add(cmbLanguage);
        Controls.Add(cmbChannel);
        Controls.Add(txtLogPath);
        Controls.Add(txtGameDir);
        Controls.Add(lblLogPath);
        Controls.Add(lblLanguage);
        Controls.Add(lblChannel);
        Controls.Add(lblGameDir);
        Controls.Add(btnReload);
        Controls.Add(btnStop);
        Controls.Add(btnStart);
        Controls.Add(txtSummary);
        Controls.Add(lblStatus);
        Controls.Add(lblTitle);
        MaximizeBox = false;
        MinimizeBox = false;
        Name = "Form1";
        StartPosition = FormStartPosition.CenterScreen;
        Text = "SCMDB Watcher Desktop";
        ResumeLayout(false);
        PerformLayout();
    }

    #endregion
}
