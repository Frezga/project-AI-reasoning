// Variabel global untuk menyimpan dataset yang diproses
let appData = null;
let profileChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
  initUploadHandlers();

  fetch("/api/results")
    .then((response) => {
      if (!response.ok) {
        return response.json().then((err) => {
          throw new Error(err.error || "Kesalahan server");
        });
      }
      return response.json();
    })
    .then((data) => {
      appData = data;
      document.getElementById("loader").style.display = "none";
      document.getElementById("dashboard-content").style.display = "block";

      initializeDashboard();
    })
    .catch((error) => {
      document.getElementById("loader").style.display = "none";
      const errorDiv = document.getElementById("error");
      errorDiv.innerText = error.message;
      errorDiv.style.display = "block";
    });
});

function switchTab(tabName) {
  // Hapus kelas aktif
  document
    .querySelectorAll(".tab-btn")
    .forEach((btn) => btn.classList.remove("active"));
  document
    .querySelectorAll(".panel")
    .forEach((p) => p.classList.remove("active"));

  // Cari tombol tab berdasarkan tabName dan aktifkan
  const btn = Array.from(document.querySelectorAll(".tab-btn")).find(b => 
    b.getAttribute("onclick") && b.getAttribute("onclick").includes(`'${tabName}'`)
  );
  if (btn) btn.classList.add("active");

  const panel = document.getElementById(`${tabName}-panel`);
  if (panel) panel.classList.add("active");
}

function initializeDashboard() {
  // 1. Mengisi nilai kartu statistik
  const nStudents = Object.keys(appData.learning_paths).length;
  document.getElementById("stat-total-students").innerText = nStudents;
  document.getElementById("stat-groups").innerText = appData.groups.length;

  const nClusters = appData.cluster_profile.length;
  document.getElementById("stat-clusters").innerText = `K = ${nClusters}`;

  // Hitung Rata-rata Penguasaan Sistem
  let totalMastery = 0;
  let count = 0;
  appData.cluster_profile.forEach((cluster) => {
    Object.values(cluster.scores).forEach((score) => {
      totalMastery += score;
      count++;
    });
  });
  const avgMastery = Math.round((totalMastery / count) * 100);
  document.getElementById("stat-avg-mastery").innerText = `${avgMastery}%`;

  // 2. Render Tabel Distribusi Klaster
  const clusterDistTbody = document.getElementById("cluster-dist-tbody");
  clusterDistTbody.innerHTML = "";

  // Hitung jumlah anggota masing-masing klaster
  const clusterSizes = {};
  Object.values(appData.cluster_labels).forEach((cid) => {
    clusterSizes[cid] = (clusterSizes[cid] || 0) + 1;
  });

  appData.cluster_profile.forEach((profile) => {
    const cid = profile.cluster_id;
    const label = profile.cluster_label;
    const size = clusterSizes[cid] || 0;

    // Hitung rata-rata P(Ln) untuk klaster ini
    const scoresList = Object.values(profile.scores);
    const avgMasteryScore = (
      scoresList.reduce((a, b) => a + b, 0) / scoresList.length
    ).toFixed(3);

    const tr = document.createElement("tr");
    tr.innerHTML = `
              <td>
                  <span class="status-badge status-${getClusterBadgeClass(label)}">${label}</span>
              </td>
              <td style="font-weight: 600;">${size} mahasiswa</td>
              <td style="color: #a5b4fc; font-weight: 600;">${Math.round(avgMasteryScore * 100)}%</td>
          `;
    clusterDistTbody.appendChild(tr);
  });

  // 3. Render Multi-Bar Chart menggunakan Chart.js
  renderClusterProfileChart();

  // 4. Render Kelompok Belajar
  renderStudyGroups();

  // 5. Isi Dropdown Pemilih Mahasiswa
  const studentSelect = document.getElementById("student-select");
  studentSelect.innerHTML = "";

  // Urutkan kunci mahasiswa berdasarkan nama secara alfabetis
  const sortedNims = Object.keys(appData.learning_paths).sort((a, b) => {
    return appData.learning_paths[a].nama.localeCompare(
      appData.learning_paths[b].nama,
    );
  });

  sortedNims.forEach((nim) => {
    const opt = document.createElement("option");
    opt.value = nim;
    opt.text = `${appData.learning_paths[nim].nama} (${nim})`;
    studentSelect.appendChild(opt);
  });

  // Muat data mahasiswa pertama secara default
  if (sortedNims.length > 0) {
    studentSelect.value = sortedNims[0];
    loadStudentPath();
  }
}

function getClusterBadgeClass(label) {
  const l = label.toLowerCase();
  if (l.includes("mahir")) return "mahir";
  if (l.includes("cukup")) return "cukup";
  return "remedial";
}

function renderClusterProfileChart() {
  const ctx = document.getElementById("profileChart").getContext("2d");

  // Ekstrak daftar topik (kolom profil penguasaan)
  const firstCluster = appData.cluster_profile[0];
  const topics = Object.keys(firstCluster.scores);

  // Tentukan palet warna dataset sesuai tema
  const colorPalettes = [
    { border: "#047857", background: "rgba(4, 120, 87, 0.15)" }, // Green (Mahir)
    { border: "#b45309", background: "rgba(180, 83, 9, 0.15)" }, // Yellow (Cukup)
    { border: "#b91c1c", background: "rgba(185, 28, 28, 0.15)" }, // Red (Remedial)
  ];

  const datasets = appData.cluster_profile.map((profile, index) => {
    const label = profile.cluster_label;
    const scores = topics.map((t) => profile.scores[t]);
    const colors = colorPalettes[index % colorPalettes.length];

    return {
      label: label,
      data: scores,
      borderColor: colors.border,
      backgroundColor: colors.background,
      borderWidth: 2,
      borderRadius: 4,
      barPercentage: 0.8,
      categoryPercentage: 0.8,
    };
  });

  if (profileChartInstance) {
    profileChartInstance.destroy();
  }

  profileChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: topics,
      datasets: datasets,
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          labels: {
            color: "#475569",
            font: {
              family: "Plus Jakarta Sans",
              size: 12,
              weight: "600",
            },
          },
        },
        tooltip: {
          callbacks: {
            label: function (context) {
              return `${context.dataset.label}: ${Math.round(context.raw * 100)}% penguasaan`;
            },
          },
        },
      },
      scales: {
        x: {
          ticks: {
            color: "#475569",
            font: { family: "Plus Jakarta Sans", size: 11 },
          },
          grid: { color: "rgba(0, 0, 0, 0.05)" },
        },
        y: {
          min: 0,
          max: 1.0,
          ticks: {
            color: "#475569",
            font: { family: "Plus Jakarta Sans", size: 11 },
            callback: function (value) {
              return value * 100 + "%";
            },
          },
          grid: { color: "rgba(0, 0, 0, 0.05)" },
        },
      },
    },
  });
}

function renderStudyGroups() {
  const container = document.getElementById("groups-container");
  container.innerHTML = "";

  appData.groups.forEach((group) => {
    const card = document.createElement("div");
    card.className = "group-card";

    // Urutkan anggota berdasarkan rata-rata penguasaan secara menurun
    const sortedMembers = [...group.anggota].sort(
      (a, b) => b.avg_mastery - a.avg_mastery,
    );

    let membersHtml = "";
    sortedMembers.forEach((m, idx) => {
      const mentorLabel =
        idx === 0
          ? '<span style="font-size: 0.7rem; font-weight: 700; background: rgba(79, 70, 229, 0.1); border: 1px solid rgba(79, 70, 229, 0.2); color: #4f46e5; padding: 0.15rem 0.4rem; border-radius: 0.25rem; margin-left: 0.5rem;">TUTOR</span>'
          : "";
      membersHtml += `
                  <div class="member-item">
                      <div class="member-info">
                          <span class="member-name">${m.nama}${mentorLabel}</span>
                          <span class="member-nim">NIM: ${m.nim}</span>
                      </div>
                      <div style="text-align: right; display: flex; flex-direction: column; align-items: flex-end; gap: 0.2rem;">
                          <span class="status-badge status-${getClusterBadgeClass(m.cluster_label)}">${m.cluster_label}</span>
                          <span style="font-size: 0.75rem; color: var(--text-secondary); font-weight: 600;">P(L) = ${Math.round(m.avg_mastery * 100)}%</span>
                      </div>
                  </div>
              `;
    });

    card.innerHTML = `
              <div class="group-header">
                  <span class="group-title">Kelompok Belajar ${group.kelompok_id}</span>
                  <span class="status-badge" style="background: rgba(79, 70, 229, 0.08); border: 1px solid rgba(79, 70, 229, 0.2); color: #4f46e5; font-weight: 700;">
                      Diversity: ${group.heterogeneity_score}
                  </span>
              </div>
              <div class="group-members">
                  ${membersHtml}
              </div>
              <div class="group-reasoning">
                  ${group.reasoning}
              </div>
          `;
    container.appendChild(card);
  });
}

function loadStudentPath() {
  const nim = document.getElementById("student-select").value;
  const studentData = appData.learning_paths[nim];

  // Dapatkan label klaster mahasiswa
  const cId = appData.cluster_labels[nim];
  const clusterInfo = appData.cluster_profile.find((p) => p.cluster_id === cId);
  const clusterLabel = clusterInfo ? clusterInfo.cluster_label : "Umum";

  // 1. Isi Kartu Ringkasan Profil (Kiri)
  const profileCard = document.getElementById("student-profile-card");

  // Hitung penguasaan secara keseluruhan
  const scoresList = studentData.path.map((p) => p.p_ln);
  const overallMastery = Math.round(
    (scoresList.reduce((a, b) => a + b, 0) / scoresList.length) * 100,
  );

  profileCard.innerHTML = `
          <h2 style="margin-bottom: 1.5rem;">Profil Mahasiswa</h2>
          <div style="display: flex; flex-direction: column; gap: 1rem; align-items: center; text-align: center; margin-bottom: 2rem;">
              <div style="width: 80px; height: 80px; border-radius: 50%; background: var(--primary-gradient); display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: 800; color: white; margin-bottom: 0.5rem;">
                  ${studentData.nama.charAt(0)}
              </div>
              <div>
                  <div style="font-size: 1.25rem; font-weight: 700;">${studentData.nama}</div>
                  <div style="color: var(--text-secondary); font-size: 0.85rem;">NIM: ${studentData.nim}</div>
              </div>
              <span class="status-badge status-${getClusterBadgeClass(clusterLabel)}" style="margin-top: 0.5rem; font-size: 0.85rem; padding: 0.4rem 1rem;">
                  Kompetensi: ${clusterLabel}
              </span>
          </div>
          
          <div style="border-top: 1px solid var(--surface-border); padding-top: 1.5rem;">
              <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
                  <span style="font-size: 0.85rem; color: var(--text-secondary);">Estimasi Penguasaan Konsep:</span>
                  <span style="font-size: 0.85rem; font-weight: 700; color: #a5b4fc;">${overallMastery}%</span>
              </div>
              <div style="width: 100%; height: 8px; background: rgba(255,255,255,0.05); border-radius: 999px; overflow: hidden;">
                  <div style="width: ${overallMastery}%; height: 100%; background: var(--primary-gradient); border-radius: 999px;"></div>
              </div>
          </div>
      `;

  // 2. Isi Rencana Pembelajaran Timeline yang Direkomendasikan (Kanan)
  const timelineContainer = document.getElementById("path-timeline-container");
  timelineContainer.innerHTML = "";

  studentData.path.forEach((step, index) => {
    const stepDiv = document.createElement("div");
    stepDiv.className = `path-step ${index === 0 ? "active-step" : ""}`;

    let statusClass = "remedial";
    if (step.status.includes("Dikuasai")) statusClass = "mahir";
    else if (step.status.includes("Penguatan")) statusClass = "cukup";

    stepDiv.innerHTML = `
              <div class="step-header">
                  <span class="step-title">${step.materi}</span>
                  <span class="step-priority">Prioritas #${step.prioritas}</span>
              </div>
              <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 0.75rem;">
                  <span class="step-score">Probabilitas Penguasaan: <strong style="color: #f3f4f6;">${Math.round(step.p_ln * 100)}%</strong></span>
                  <span class="status-badge status-${statusClass}">${step.status}</span>
              </div>
          `;
    timelineContainer.appendChild(stepDiv);
  });
}

// ==========================================================================
// KODE KELOLA UNGGAHAN DATASET (CSV & EXCEL)
// ==========================================================================

let uploadedFiles = {
  mahasiswa: null,
  kuis: null,
  log: null
};

let fileValidationStatus = {
  mahasiswa: false,
  kuis: false,
  log: false
};

function initUploadHandlers() {
  const uploadKeys = ['mahasiswa', 'kuis', 'log'];
  
  uploadKeys.forEach(key => {
    const dropzone = document.getElementById(`dropzone-${key}`);
    const input = document.getElementById(`file-${key}`);
    
    if (!dropzone || !input) return;

    // Klik dropzone untuk memilih berkas
    dropzone.addEventListener('click', (e) => {
      // Pastikan input file diklik, cegah perulangan event click
      if (e.target !== input) {
        input.click();
      }
    });

    // Perubahan file input
    input.addEventListener('change', (e) => {
      if (e.target.files.length > 0) {
        handleFileSelection(key, e.target.files[0]);
      }
    });

    // Drag-and-drop events
    dropzone.addEventListener('dragover', (e) => {
      e.preventDefault();
      dropzone.classList.add('dragover');
    });

    dropzone.addEventListener('dragleave', () => {
      dropzone.classList.remove('dragover');
    });

    dropzone.addEventListener('drop', (e) => {
      e.preventDefault();
      dropzone.classList.remove('dragover');
      if (e.dataTransfer.files.length > 0) {
        handleFileSelection(key, e.dataTransfer.files[0]);
      }
    });

    // Event click untuk tombol X (hapus file)
    const removeBtn = dropzone.querySelector('.btn-remove-file');
    if (removeBtn) {
      removeBtn.addEventListener('click', (e) => {
        e.stopPropagation(); // mencegah membuka file dialog
        clearFileSelection(key);
      });
    }
  });
}

function handleFileSelection(key, file) {
  if (!file) return;

  const dropzone = document.getElementById(`dropzone-${key}`);
  const filePrompt = dropzone.querySelector('.dropzone-prompt');
  const fileInfo = dropzone.querySelector('.file-info');
  const fileNameSpan = fileInfo.querySelector('.file-name');
  const fileStatusSpan = fileInfo.querySelector('.file-status');

  // Reset status validasi per file terlebih dahulu
  fileValidationStatus[key] = false;
  uploadedFiles[key] = null;
  updateProcessButtonState();

  // Validasi ekstensi
  const extension = file.name.split('.').pop().toLowerCase();
  if (extension !== 'csv' && extension !== 'xlsx' && extension !== 'xls') {
    showFileStatus(dropzone, filePrompt, fileInfo, fileNameSpan, fileStatusSpan, file.name, "Error: Ekstensi file tidak didukung", "remedial");
    return;
  }

  // Set nama berkas
  fileNameSpan.innerText = file.name;

  if (extension === 'xlsx' || extension === 'xls') {
    // File excel divalidasi langsung di server
    showFileStatus(dropzone, filePrompt, fileInfo, fileNameSpan, fileStatusSpan, file.name, "Format Excel", "info");
    uploadedFiles[key] = file;
    fileValidationStatus[key] = true;
    updateProcessButtonState();
  } else {
    // File CSV divalidasi client-side terlebih dahulu
    validateCSVClientSide(key, file, (isValid, errorMsg) => {
      if (isValid) {
        showFileStatus(dropzone, filePrompt, fileInfo, fileNameSpan, fileStatusSpan, file.name, "Format CSV Valid", "mahir");
        uploadedFiles[key] = file;
        fileValidationStatus[key] = true;
      } else {
        showFileStatus(dropzone, filePrompt, fileInfo, fileNameSpan, fileStatusSpan, file.name, `Error: ${errorMsg}`, "remedial");
      }
      updateProcessButtonState();
    });
  }
}

function showFileStatus(dropzone, prompt, info, nameSpan, statusSpan, fileName, statusText, badgeType) {
  prompt.style.display = 'none';
  info.style.display = 'flex';
  nameSpan.innerText = fileName;
  
  statusSpan.className = 'file-status status-badge';
  if (badgeType === 'mahir') {
    statusSpan.classList.add('status-mahir');
  } else if (badgeType === 'remedial') {
    statusSpan.classList.add('status-remedial');
  } else {
    statusSpan.classList.add('status-info');
  }
  statusSpan.innerText = statusText;
}

function validateCSVClientSide(key, file, callback) {
  const reader = new FileReader();
  reader.onload = function(e) {
    const text = e.target.result;
    const firstLine = text.split('\n')[0].trim();
    
    if (!firstLine) {
      callback(false, "File CSV kosong");
      return;
    }

    // Ekstrak nama kolom
    const cols = firstLine.split(',').map(c => c.trim().replace(/^["']|["']$/g, ''));

    // Kolom wajib masing-masing tabel
    let required = [];
    if (key === 'mahasiswa') {
      required = ['NIM', 'Nama'];
    } else if (key === 'kuis') {
      required = ['ID_Soal', 'Materi', 'Submateri', 'Bobot', 'Opsi_A', 'Opsi_B', 'Opsi_C', 'Opsi_D', 'Kunci'];
    } else if (key === 'log') {
      required = ['NIM', 'ID_Soal', 'Jawaban_Mahasiswa', 'Skor_Biner'];
    }

    const missing = required.filter(col => !cols.includes(col));
    if (missing.length > 0) {
      callback(false, `Kolom kurang: ${missing.join(', ')}`);
    } else {
      callback(true, null);
    }
  };

  reader.onerror = function() {
    callback(false, "Gagal membaca file");
  };

  // Hanya baca 2KB pertama dari file CSV (cukup untuk header saja)
  const slice = file.slice(0, 2048);
  reader.readAsText(slice);
}

function updateProcessButtonState() {
  const btn = document.getElementById('btn-process-upload');
  if (!btn) return;
  
  const allValid = fileValidationStatus.mahasiswa && fileValidationStatus.kuis && fileValidationStatus.log;
  btn.disabled = !allValid;
}

function submitUploadedFiles() {
  const btn = document.getElementById('btn-process-upload');
  const resetBtn = document.getElementById('btn-reset-data');

  if (!uploadedFiles.mahasiswa || !uploadedFiles.kuis || !uploadedFiles.log) {
    showUploadMessage("Error: Silakan unggah ketiga berkas terlebih dahulu.", "error");
    return;
  }

  btn.disabled = true;
  resetBtn.disabled = true;
  showUploadMessage("Sedang mengunggah, memvalidasi relasi data, dan memproses dashboard...", "info");

  const formData = new FormData();
  formData.append('mahasiswa', uploadedFiles.mahasiswa);
  formData.append('kuis', uploadedFiles.kuis);
  formData.append('log', uploadedFiles.log);

  fetch('/api/upload', {
    method: 'POST',
    body: formData
  })
  .then(res => res.json().then(data => ({ status: res.status, data })))
  .then(({ status, data }) => {
    if (status !== 200) {
      throw new Error(data.error || "Gagal memperbarui dataset");
    }
    
    showUploadMessage(data.message, "success");
    
    // Tarik data hasil pipeline yang baru diperbarui
    return fetch("/api/results");
  })
  .then(res => {
    if (!res.ok) throw new Error("Gagal mengambil data baru");
    return res.json();
  })
  .then(data => {
    appData = data;
    initializeDashboard();
    
    // Reset status form upload
    resetUploadFormStates();
    
    // Alihkan ke halaman ringkasan dosen setelah 1.5 detik
    setTimeout(() => {
      switchTab('overview');
      btn.disabled = false;
      resetBtn.disabled = false;
    }, 1500);
  })
  .catch(err => {
    showUploadMessage(err.message, "error");
    btn.disabled = false;
    resetBtn.disabled = false;
  });
}

function resetToDefaultData() {
  const btn = document.getElementById('btn-process-upload');
  const resetBtn = document.getElementById('btn-reset-data');

  if (!confirm("Apakah Anda yakin ingin mereset seluruh data kembali ke data dummy bawaan?")) {
    return;
  }

  btn.disabled = true;
  resetBtn.disabled = true;
  showUploadMessage("Sedang mengembalikan data ke bawaan dummy...", "info");

  fetch('/api/reset', {
    method: 'POST'
  })
  .then(res => res.json().then(data => ({ status: res.status, data })))
  .then(({ status, data }) => {
    if (status !== 200) {
      throw new Error(data.error || "Gagal mereset data");
    }
    
    showUploadMessage("Dataset berhasil direset!", "success");
    
    // Tarik data dashboard yang baru direset
    return fetch("/api/results");
  })
  .then(res => {
    if (!res.ok) throw new Error("Gagal mengambil data baru");
    return res.json();
  })
  .then(data => {
    appData = data;
    initializeDashboard();
    
    resetUploadFormStates();
    
    setTimeout(() => {
      switchTab('overview');
      btn.disabled = false;
      resetBtn.disabled = false;
    }, 1500);
  })
  .catch(err => {
    showUploadMessage(err.message, "error");
    btn.disabled = false;
    resetBtn.disabled = false;
  });
}

function resetUploadFormStates() {
  uploadedFiles = { mahasiswa: null, kuis: null, log: null };
  fileValidationStatus = { mahasiswa: false, kuis: false, log: false };
  updateProcessButtonState();

  const keys = ['mahasiswa', 'kuis', 'log'];
  keys.forEach(key => {
    const dropzone = document.getElementById(`dropzone-${key}`);
    const prompt = dropzone.querySelector('.dropzone-prompt');
    const info = dropzone.querySelector('.file-info');
    const input = document.getElementById(`file-${key}`);
    
    input.value = "";
    prompt.style.display = 'block';
    info.style.display = 'none';
  });

  const msgBox = document.getElementById('upload-message');
  msgBox.style.display = 'none';
}

function clearFileSelection(key) {
  uploadedFiles[key] = null;
  fileValidationStatus[key] = false;
  updateProcessButtonState();

  const dropzone = document.getElementById(`dropzone-${key}`);
  const prompt = dropzone.querySelector('.dropzone-prompt');
  const info = dropzone.querySelector('.file-info');
  const input = document.getElementById(`file-${key}`);
  
  input.value = "";
  prompt.style.display = 'block';
  info.style.display = 'none';
}

function showUploadMessage(msg, type) {
  const msgBox = document.getElementById('upload-message');
  msgBox.innerText = msg;
  msgBox.style.display = 'block';
  
  msgBox.className = 'upload-message-box';
  if (type === 'success') {
    msgBox.classList.add('upload-msg-success');
  } else if (type === 'error') {
    msgBox.classList.add('upload-msg-error');
  } else {
    msgBox.classList.add('upload-msg-info');
  }
}

