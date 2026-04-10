import { auth, db } from "./firebase.js";
import {
    onAuthStateChanged,
    signOut
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-auth.js";
import {
    doc,
    getDoc,
    collection,
    onSnapshot
} from "https://www.gstatic.com/firebasejs/10.12.2/firebase-firestore.js";

const state = {
    students: [],
    selectedSegment: "all",
    selectedPrediction: "all"
};

const elements = {
    logoutLink: document.getElementById("logoutLink"),
    connectionStatus: document.getElementById("connectionStatus"),
    lastUpdated: document.getElementById("lastUpdated"),
    adminIdentity: document.getElementById("adminIdentity"),
    totalStudents: document.getElementById("totalStudents"),
    placementCount: document.getElementById("placementCount"),
    higherStudiesCount: document.getElementById("higherStudiesCount"),
    highRiskCount: document.getElementById("highRiskCount"),
    averageCgpa: document.getElementById("averageCgpa"),
    segmentHighPotential: document.getElementById("segmentHighPotential"),
    segmentPlacementReady: document.getElementById("segmentPlacementReady"),
    segmentHighRisk: document.getElementById("segmentHighRisk"),
    attentionCountLabel: document.getElementById("attentionCountLabel"),
    riskAlerts: document.getElementById("riskAlerts"),
    placementAnalyticsLabel: document.getElementById("placementAnalyticsLabel"),
    higherStudiesAnalyticsLabel: document.getElementById("higherStudiesAnalyticsLabel"),
    placementAnalyticsBar: document.getElementById("placementAnalyticsBar"),
    higherStudiesAnalyticsBar: document.getElementById("higherStudiesAnalyticsBar"),
    segmentBreakdown: document.getElementById("segmentBreakdown"),
    segmentFilter: document.getElementById("segmentFilter"),
    predictionFilter: document.getElementById("predictionFilter"),
    studentsTableBody: document.getElementById("studentsTableBody")
};

elements.logoutLink.addEventListener("click", async (event) => {
    event.preventDefault();
    await signOut(auth);
    window.location.href = "/admin-login";
});

elements.segmentFilter.addEventListener("change", (event) => {
    state.selectedSegment = event.target.value;
    renderStudentTable();
});

elements.predictionFilter.addEventListener("change", (event) => {
    state.selectedPrediction = event.target.value;
    renderStudentTable();
});

onAuthStateChanged(auth, async (user) => {
    if (!user) {
        window.location.href = "/admin-login";
        return;
    }

    try {
        const userRef = doc(db, "users", user.uid);
        const userSnapshot = await getDoc(userRef);
        const role = userSnapshot.exists() ? userSnapshot.data().role : "";

        if (role !== "admin") {
            await signOut(auth);
            window.location.href = "/admin-login";
            return;
        }

        elements.adminIdentity.textContent = user.email || "Admin user";
        subscribeToStudents();
    } catch (error) {
        console.error("Admin role check failed:", error);
        elements.connectionStatus.textContent = "Admin verification failed";
    }
});

function subscribeToStudents() {
    elements.connectionStatus.textContent = "Live";

    // Real-time Firestore stream for the students collection.
    onSnapshot(
        collection(db, "students"),
        (snapshot) => {
            state.students = snapshot.docs.map((snapshotDoc) => ({
                id: snapshotDoc.id,
                ...snapshotDoc.data()
            }));

            renderDashboard();
        },
        (error) => {
            console.error("Students stream failed:", error);
            elements.connectionStatus.textContent = "Connection error";
            renderEmptyDashboard("Unable to load students. Check Firestore permissions and browser console.");
        }
    );
}

function renderDashboard() {
    const derivedStudents = state.students.map(deriveStudentFlags);
    renderSummaryCards(derivedStudents);
    renderSegmentation(derivedStudents);
    renderRiskAlerts(derivedStudents);
    renderAnalytics(derivedStudents);
    renderStudentTable(derivedStudents);
    elements.lastUpdated.textContent = formatTime(new Date());
}

function deriveStudentFlags(student) {
    const cgpa = Number(student.cgpa) || 0;
    const aptitude = Number(student.aptitude_score) || 0;
    const arrears = Number(student.arrears_count) || 0;
    const internship = Number(student.internship_duration) || 0;
    const programming = Number(student.skills?.programming) || 0;
    const prediction = student.prediction?.career || "needs_training";

    const isHighRisk = cgpa < 6 || aptitude < 40 || arrears > 2;

    let segment = "general";
    if (cgpa > 8 && programming < 5) {
        segment = "high_potential";
    } else if (cgpa > 7 && programming >= 6) {
        segment = "placement_ready";
    } else if (isHighRisk) {
        segment = "high_risk";
    }

    return {
        ...student,
        cgpa,
        aptitude,
        arrears,
        internship,
        programming,
        prediction,
        isHighRisk,
        segment
    };
}

function renderSummaryCards(students) {
    const totalStudents = students.length;
    const placementCount = students.filter((student) => student.prediction === "placement").length;
    const higherStudiesCount = students.filter((student) => student.prediction === "higher_studies").length;
    const highRiskCount = students.filter((student) => student.isHighRisk).length;
    const averageCgpa = totalStudents ? students.reduce((sum, student) => sum + student.cgpa, 0) / totalStudents : 0;

    elements.totalStudents.textContent = totalStudents;
    elements.placementCount.textContent = placementCount;
    elements.higherStudiesCount.textContent = higherStudiesCount;
    elements.highRiskCount.textContent = highRiskCount;
    elements.averageCgpa.textContent = averageCgpa.toFixed(1);
}

function renderSegmentation(students) {
    const highPotential = students.filter((student) => student.segment === "high_potential");
    const placementReady = students.filter((student) => student.segment === "placement_ready");
    const highRisk = students.filter((student) => student.segment === "high_risk");

    elements.segmentHighPotential.textContent = highPotential.length;
    elements.segmentPlacementReady.textContent = placementReady.length;
    elements.segmentHighRisk.textContent = highRisk.length;

    const cards = [
        {
            title: "High Potential",
            count: highPotential.length,
            text: "Strong academics with technical improvement opportunity."
        },
        {
            title: "Placement Ready",
            count: placementReady.length,
            text: "Students likely ready for hiring pipelines."
        },
        {
            title: "High Risk",
            count: highRisk.length,
            text: "Immediate intervention recommended."
        }
    ];

    elements.segmentBreakdown.innerHTML = cards.map((card) => `
        <div class="segment-item">
            <h3>${card.title} · ${card.count}</h3>
            <p>${card.text}</p>
        </div>
    `).join("");
}

function renderRiskAlerts(students) {
    const riskyStudents = students.filter((student) => student.isHighRisk);
    elements.attentionCountLabel.textContent = `${riskyStudents.length} student${riskyStudents.length === 1 ? "" : "s"} flagged`;

    if (!riskyStudents.length) {
        elements.riskAlerts.innerHTML = `<div class="empty-state">No students currently match the high-risk rule set.</div>`;
        return;
    }

    elements.riskAlerts.innerHTML = riskyStudents.map((student) => `
        <div class="alert-item">
            <h3>${student.name || "Unnamed Student"}</h3>
            <p>${student.email || "No email available"}</p>
            <p>CGPA ${student.cgpa.toFixed(1)} · Aptitude ${student.aptitude} · Arrears ${student.arrears}</p>
        </div>
    `).join("");
}

function renderAnalytics(students) {
    const totalStudents = students.length || 1;
    const placementCount = students.filter((student) => student.prediction === "placement").length;
    const higherStudiesCount = students.filter((student) => student.prediction === "higher_studies").length;

    const placementRatio = (placementCount / totalStudents) * 100;
    const higherStudiesRatio = (higherStudiesCount / totalStudents) * 100;

    elements.placementAnalyticsLabel.textContent = `${placementCount} (${placementRatio.toFixed(1)}%)`;
    elements.higherStudiesAnalyticsLabel.textContent = `${higherStudiesCount} (${higherStudiesRatio.toFixed(1)}%)`;
    elements.placementAnalyticsBar.style.width = `${placementRatio}%`;
    elements.higherStudiesAnalyticsBar.style.width = `${higherStudiesRatio}%`;
}

function renderStudentTable(precomputedStudents = null) {
    const students = precomputedStudents || state.students.map(deriveStudentFlags);
    const filteredStudents = students.filter((student) => {
        const segmentMatch = state.selectedSegment === "all" || student.segment === state.selectedSegment;
        const predictionMatch = state.selectedPrediction === "all" || student.prediction === state.selectedPrediction;
        return segmentMatch && predictionMatch;
    });

    if (!filteredStudents.length) {
        elements.studentsTableBody.innerHTML = `
            <tr>
                <td colspan="9" class="empty-state">No students match the current filters.</td>
            </tr>
        `;
        return;
    }

    elements.studentsTableBody.innerHTML = filteredStudents.map((student) => `
        <tr>
            <td>
                <strong>${student.name || "Unnamed Student"}</strong>
            </td>
            <td>${student.email || "-"}</td>
            <td>${student.cgpa.toFixed(1)}</td>
            <td>${renderPredictionBadge(student.prediction)}</td>
            <td>${renderSegmentBadge(student.segment)}</td>
            <td>${renderRiskBadge(student.isHighRisk)}</td>
            <td>${student.aptitude}</td>
            <td>${student.arrears}</td>
            <td>${student.internship}</td>
        </tr>
    `).join("");
}

function renderPredictionBadge(prediction) {
    const label = {
        placement: "Placement",
        higher_studies: "Higher Studies",
        needs_training: "Needs Training"
    }[prediction] || "Unknown";

    const className = {
        placement: "prediction-placement",
        higher_studies: "prediction-higher",
        needs_training: "prediction-training"
    }[prediction] || "prediction-training";

    return `<span class="badge ${className}">${label}</span>`;
}

function renderSegmentBadge(segment) {
    const label = {
        high_potential: "High Potential",
        placement_ready: "Placement Ready",
        high_risk: "High Risk",
        general: "General"
    }[segment] || "General";

    const className = {
        high_potential: "segment-high",
        placement_ready: "segment-ready",
        high_risk: "segment-risk",
        general: "segment-high"
    }[segment] || "segment-high";

    return `<span class="badge ${className}">${label}</span>`;
}

function renderRiskBadge(isHighRisk) {
    return isHighRisk
        ? `<span class="badge risk-yes">Yes</span>`
        : `<span class="badge risk-no">No</span>`;
}

function renderEmptyDashboard(message) {
    elements.totalStudents.textContent = "0";
    elements.placementCount.textContent = "0";
    elements.higherStudiesCount.textContent = "0";
    elements.highRiskCount.textContent = "0";
    elements.averageCgpa.textContent = "0.0";
    elements.segmentHighPotential.textContent = "0";
    elements.segmentPlacementReady.textContent = "0";
    elements.segmentHighRisk.textContent = "0";
    elements.attentionCountLabel.textContent = "0 students flagged";
    elements.riskAlerts.innerHTML = `<div class="empty-state">${message}</div>`;
    elements.segmentBreakdown.innerHTML = `<div class="empty-state">${message}</div>`;
    elements.studentsTableBody.innerHTML = `
        <tr>
            <td colspan="9" class="empty-state">${message}</td>
        </tr>
    `;
}

function formatTime(date) {
    return new Intl.DateTimeFormat("en-IN", {
        hour: "numeric",
        minute: "2-digit",
        second: "2-digit"
    }).format(date);
}
