// Variabel global untuk menyimpan dataset yang diproses
let appData = null;
let profileChartInstance = null;

document.addEventListener("DOMContentLoaded", () => {
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

  // Atur sebagai aktif
  event.target.classList.add("active");
  document.getElementById(`${tabName}-panel`).classList.add("active");
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
