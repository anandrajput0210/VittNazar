const analyzeButton = document.getElementById("analyze-btn");
const pitchInput = document.getElementById("pitch");
const documentInput = document.getElementById("official-document");
const documentFile =
    document.getElementById("document-file");
    let uploadedDocumentFilename = "";
let uploadedDocumentFingerprint = "";
const extractButton =
    document.getElementById("extract-btn");

const fileStatus =
    document.getElementById("file-status");
const resultsSection = document.getElementById("results");
const receiptId = document.getElementById("receipt-id");
const copyReceiptIdButton =
    document.getElementById("copy-receipt-id");
const receiptIdInput =
    document.getElementById("receipt-id-input");

const lookupReceiptButton =
    document.getElementById("lookup-receipt-btn");

const lookupStatus =
    document.getElementById("lookup-status");
const printReceiptButton =
    document.getElementById("print-receipt");

const savePdfButton =
    document.getElementById("save-pdf");
const languageEnButton =
    document.getElementById("language-en");

const languageHiButton =
    document.getElementById("language-hi");

const tagline =
    document.getElementById("tagline");
const heroTitle =
    document.getElementById("hero-title");

const heroDescription =
    document.getElementById("hero-description");

const salesTitle =
    document.getElementById("sales-title");

const salesHelper =
    document.getElementById("sales-helper");

const documentTitle =
    document.getElementById("document-title");

const documentHelper =
    document.getElementById("document-helper");

const lookupTitle =
    document.getElementById("lookup-title");

const lookupHelper =
    document.getElementById("lookup-helper");
const receiptTitle =
    document.getElementById("receipt-title");

const pressureTitle =
    document.getElementById("pressure-title");

const pressureHelper =
    document.getElementById("pressure-helper");
const footerText =
    document.querySelector("footer");
const downloadReceiptButton =
    document.getElementById("download-receipt");
const summary = document.getElementById("summary");
const documentMetadata =
    document.getElementById("document-metadata");

const documentFilename =
    document.getElementById("document-filename");

const documentFingerprint =
    document.getElementById("document-fingerprint");
const resultItems = document.getElementById("result-items");
const pressureSection =
    document.getElementById("pressure-section");

const pressureItems =
    document.getElementById("pressure-items");
const errorMessage = document.getElementById("error-message");
let currentReceipt = null;


analyzeButton.addEventListener("click", analyzePitch);

extractButton.addEventListener(
    "click",
    extractPdf
);

languageEnButton.addEventListener(
    "click",
    () => setLanguage("en")
);

languageHiButton.addEventListener(
    "click",
    () => setLanguage("hi")
);

lookupReceiptButton.addEventListener(
    "click",
    lookupReceipt
);

async function analyzePitch() {
    const pitch = pitchInput.value.trim();
    const officialDocument = documentInput.value.trim();

    errorMessage.textContent = "";

    if (!pitch) {
    errorMessage.textContent =
        languageHiButton.classList.contains("active")
            ? "कृपया बिक्री संदेश दर्ज करें।"
            : "Please enter the sales pitch.";
    return;
}

    if (!officialDocument) {
    errorMessage.textContent =
        languageHiButton.classList.contains("active")
            ? "कृपया आधिकारिक दस्तावेज़ का पाठ दर्ज करें।"
            : "Please enter the official document text.";
    return;
}

    analyzeButton.disabled = true;
    analyzeButton.textContent = "Analyzing...";

    try {
        const response = await fetch(
            "/api/analyze",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
    pitch: pitch,
    official_document: officialDocument,
    document_filename: uploadedDocumentFilename,
document_fingerprint: uploadedDocumentFingerprint
})
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Analysis failed.");
        }

        displayReceipt(data.receipt);

    } catch (error) {
        errorMessage.textContent = error.message;
    } finally {
    analyzeButton.disabled = false;

    if (languageHiButton.classList.contains("active")) {
        analyzeButton.textContent =
            "VittNazar से जाँच करें";
    } else {
        analyzeButton.textContent =
            "Analyze with VittNazar";
    }
}
}


function displayReceipt(receipt) {
    currentReceipt = receipt;

    receiptTitle.textContent =
    languageHiButton.classList.contains("active")
        ? "वादा रसीद"
        : "Promise Receipt";

const verifiedDocumentTitle =
    documentMetadata.querySelector("h3");

if (verifiedDocumentTitle) {
    verifiedDocumentTitle.textContent =
        languageHiButton.classList.contains("active")
            ? "सत्यापित दस्तावेज़"
            : "Verified Document";
}
    
    resultsSection.classList.remove("hidden");

    receiptId.textContent =
    languageHiButton.classList.contains("active")
        ? `रसीद ID: ${receipt.receipt_id}`
        : `Receipt ID: ${receipt.receipt_id}`;
    copyReceiptIdButton.classList.remove("hidden");

copyReceiptIdButton.onclick = () => {
    copyReceiptId(receipt.receipt_id);
};
    printReceiptButton.classList.remove("hidden");
savePdfButton.classList.remove("hidden");

printReceiptButton.onclick = () => {
    printReceipt(receipt);
};

savePdfButton.onclick = () => {
    saveReceiptAsPdf(receipt);
};

    const counts = receipt.summary;
    const evidenceLabel =
    languageHiButton.classList.contains("active")
        ? "दस्तावेज़ प्रमाण"
        : "Document evidence";

const pageLabel =
    languageHiButton.classList.contains("active")
        ? "पृष्ठ"
        : "Page";

const clarificationLabel =
    languageHiButton.classList.contains("active")
        ? "स्पष्टीकरण प्रश्न"
        : "Clarification question";

const hindi =
    languageHiButton.classList.contains("active");

summary.innerHTML = `
    <div class="summary-box">
        ${hindi ? "कुल" : "Total"}: ${counts.total_claims}
    </div>

    <div class="summary-box">
        ${hindi ? "दस्तावेज़ द्वारा समर्थित" : "Supported"}: ${counts.supported}
    </div>

    <div class="summary-box">
        ${hindi ? "विरोधाभासी" : "Conflicts"}: ${counts.contradicted}
    </div>

    <div class="summary-box">
        ${hindi ? "जाँच आवश्यक" : "Needs review"}: ${counts.not_found}
    </div>

    <div class="summary-box">
        ${hindi ? "आंशिक रूप से समर्थित" : "Partial"}:
        ${counts.partially_supported || 0}
    </div>
`;

    resultItems.innerHTML = "";

    receipt.items.forEach(item => {
        const result = document.createElement("div");

        result.className = "result-item";

        result.innerHTML = `
            <h4>${escapeHtml(item.claim)}</h4>

            <span class="status status-${item.status}">
                ${formatStatus(item.status)}
            </span>

            <p>${escapeHtml(item.reason)}</p>

            <div class="evidence">
    <strong>${evidenceLabel}</strong>

    ${
        item.evidence_page
            ? `<div class="evidence-page">
                ${pageLabel} ${item.evidence_page}
               </div>`
            : ""
    }

    <p>${escapeHtml(item.evidence)}</p>
</div>

            <div class="question">
                ${clarificationLabel}:
                <br>
                ${escapeHtml(item.clarification_question)}
            </div>
        `;

        resultItems.appendChild(result);
    });

    displayPressureSignals(receipt.pressure_signals);

    resultsSection.scrollIntoView({
        behavior: "smooth"
    });
    const documentInfo = receipt.document;

if (
    documentInfo &&
    documentInfo.filename &&
    documentInfo.fingerprint
) {
    documentFilename.textContent =
    languageHiButton.classList.contains("active")
        ? `फ़ाइल नाम: ${documentInfo.filename}`
        : `Filename: ${documentInfo.filename}`;

    documentFingerprint.textContent =
    `SHA-256: ${documentInfo.fingerprint}`;

    documentMetadata.classList.remove("hidden");
} else {
    documentMetadata.classList.add("hidden");
    

    documentFilename.textContent = "";
    documentFingerprint.textContent = "";
}
}

function formatStatus(status) {
    const hindi =
        languageHiButton.classList.contains("active");

    if (hindi) {
        const labelsHi = {
            supported: "दस्तावेज़ द्वारा समर्थित",
            contradicted: "दस्तावेज़ से मेल नहीं खाता",
            partially_supported: "आंशिक रूप से समर्थित",
            not_found: "जाँच आवश्यक"
        };

        return labelsHi[status] || status;
    }

    const labelsEn = {
        supported: "Supported by document",
        contradicted: "Conflicts with document",
        partially_supported: "Partially supported",
        not_found: "Needs verification"
    };

    return labelsEn[status] || status;
}

function escapeHtml(value) {
    return String(value)
        .replaceAll("&", "&amp;")
        .replaceAll("<", "&lt;")
        .replaceAll(">", "&gt;")
        .replaceAll('"', "&quot;")
        .replaceAll("'", "&#039;");
}
function displayPressureSignals(signals) {
    pressureItems.innerHTML = "";

    if (!signals || signals.length === 0) {
        pressureSection.classList.add("hidden");
        return;
    }

    pressureSection.classList.remove("hidden");

    signals.forEach(signal => {
        const item = document.createElement("div");

        item.className = "pressure-item";
        
        const hindi =
    languageHiButton.classList.contains("active");

const labelHi = {
    urgency: "तात्कालिकता / समय का दबाव",
    guaranteed_outcome: "गारंटीकृत परिणाम वाली भाषा",
    fear_of_missing_out: "मौका छूटने का डर"
};

const explanationHi = {
    urgency:
        "संदेश में समय का ऐसा दबाव है जो निवेशक को जल्दबाज़ी में वित्तीय निर्णय लेने के लिए प्रेरित कर सकता है.",

    guaranteed_outcome:
        "संदेश किसी वित्तीय परिणाम को निश्चित या बिना जोखिम वाला बताता है.",

    fear_of_missing_out:
        "संदेश यह संकेत देता है कि तुरंत कार्रवाई न करने पर निवेशक किसी विशेष अवसर से चूक सकता है."
};

const signalLabel =
    hindi
        ? (labelHi[signal.category] || signal.label)
        : signal.label;

const signalExplanation =
    hindi
        ? (explanationHi[signal.category] || signal.explanation)
        : signal.explanation;
        item.innerHTML = `
            <strong>${escapeHtml(signalLabel)}</strong>

            <span class="pressure-match">
                "${escapeHtml(signal.matched_text)}"
            </span>

            <p>${escapeHtml(signalExplanation)}</p>
        `;

        pressureItems.appendChild(item);
    });
}
async function extractPdf() {
    const file = documentFile.files[0];

    fileStatus.textContent = "";

    if (!file) {
    fileStatus.textContent =
        languageHiButton.classList.contains("active")
            ? "कृपया पहले एक PDF चुनें।"
            : "Please select a PDF first.";
    return;
}

    if (file.type !== "application/pdf") {
    fileStatus.textContent =
        languageHiButton.classList.contains("active")
            ? "केवल PDF फ़ाइलें समर्थित हैं।"
            : "Only PDF files are supported.";
    return;
}

    extractButton.disabled = true;
    extractButton.textContent = "Extracting...";

    try {
        const formData = new FormData();

        formData.append("file", file);

        const response = await fetch(
            "/api/extract-document",
            {
                method: "POST",
                body: formData
            }
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "PDF extraction failed."
            );
        }

        documentInput.value = data.text;
        uploadedDocumentFilename = data.filename;
uploadedDocumentFingerprint = data.document_fingerprint;
        fileStatus.textContent =
    languageHiButton.classList.contains("active")
        ? `${data.filename} सफलतापूर्वक निकाली गई (${data.characters} अक्षर)।`
        : `${data.filename} extracted successfully (${data.characters} characters).`;

    } catch (error) {
    const hindi =
        languageHiButton.classList.contains("active");

    const hindiErrors = {
        "Please select a PDF first.":
            "कृपया पहले एक PDF चुनें।",

        "Only PDF files are supported.":
            "केवल PDF फ़ाइलें समर्थित हैं।",

        "Uploaded PDF is empty.":
            "अपलोड की गई PDF खाली है।",

        "The uploaded file is not a valid PDF.":
            "अपलोड की गई फ़ाइल एक मान्य PDF नहीं है।",

        "PDF file is too large. Maximum allowed size is 10 MB.":
            "PDF फ़ाइल बहुत बड़ी है। अधिकतम आकार 10 MB है।",

        "No extractable text was found in the PDF.":
            "PDF में निकालने योग्य पाठ नहीं मिला।"
    };

    fileStatus.textContent =
        hindi
            ? (
                hindiErrors[error.message]
                || "PDF संसाधित नहीं की जा सकी।"
            )
            : error.message;

    // Prevent stale document text from being analyzed.
    documentInput.value = "";

    uploadedDocumentFilename = "";
    uploadedDocumentFingerprint = "";
}finally {
    extractButton.disabled = false;

    if (languageHiButton.classList.contains("active")) {
        extractButton.textContent =
            "PDF निकालें";
    } else {
        extractButton.textContent =
            "Extract PDF";
    }
}
}

function buildReceiptHtml(receipt, includeActions = true) {
    const counts = receipt.summary;

    const documentInfo = receipt.document;

const documentHtml = (
    documentInfo &&
    documentInfo.filename &&
    documentInfo.fingerprint
)
    ? `
        <div class="document-info">
            <h2>Verified Document</h2>

            <p>
                <strong>Filename:</strong>
                ${escapeHtml(documentInfo.filename)}
            </p>

            <p>
                <strong>SHA-256:</strong>
                ${escapeHtml(documentInfo.fingerprint)}
            </p>
        </div>
    `
    : "";
    const claimsHtml = receipt.items.map(item => `
        <div class="claim">
            <h3>${escapeHtml(item.claim)}</h3>

            <div class="status">
                ${escapeHtml(formatStatus(item.status))}
            </div>

            <p>
                ${escapeHtml(item.reason)}
            </p>

            <div class="evidence">
                <strong>
    ${
        languageHiButton.classList.contains("active")
            ? "दस्तावेज़ प्रमाण"
            : "Document evidence"
    }
</strong>
                ${
                    item.evidence_page
                        ? `<span class="page">
                            ${
    languageHiButton.classList.contains("active")
        ? "पृष्ठ"
        : "Page"
} ${item.evidence_page}
                           </span>`
                        : ""
                }

                <p>${escapeHtml(item.evidence)}</p>
            </div>

            <div class="question">
                <strong>${
    languageHiButton.classList.contains("active")
        ? "स्पष्टीकरण प्रश्न"
        : "Clarification question"
}:</strong>
                <p>${escapeHtml(item.clarification_question)}</p>
            </div>
        </div>
    `).join("");

    const pressureHtml = (
        receipt.pressure_signals &&
        receipt.pressure_signals.length
    )
        ? `
            <section>
                <h2>Pressure Signals</h2>

                <p class="helper">
                    These are persuasion patterns detected in the
                    sales message. They are not proof of wrongdoing.
                </p>

                ${receipt.pressure_signals.map(signal => `
                    <div class="pressure">
                        <strong>
                            ${escapeHtml(signal.label)}
                        </strong>

                        <span>
                            "${escapeHtml(signal.matched_text)}"
                        </span>

                        <p>
                            ${escapeHtml(signal.explanation)}
                        </p>
                    </div>
                `).join("")}
            </section>
        `
        : "";

    const html = `
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>VittNazar Promise Receipt</title>

    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 900px;
            margin: 40px auto;
            padding: 0 24px;
            color: #111827;
            line-height: 1.5;
        }

        h1 {
            margin-bottom: 4px;
        }

        .subtitle {
            color: #4b5563;
            margin-top: 0;
        }

        .receipt-id {
            margin-top: 24px;
            padding: 12px;
            background: #f3f4f6;
            border-radius: 8px;
        }

        .summary {
            display: grid;
            grid-template-columns: repeat(5, 1fr);
            gap: 10px;
            margin: 20px 0;
        }

        .summary-box {
            padding: 12px;
            background: #f3f4f6;
            border-radius: 8px;
            text-align: center;
        }

        section {
            margin-top: 28px;
        }

        .claim {
            border: 1px solid #d1d5db;
            border-radius: 10px;
            padding: 18px;
            margin: 16px 0;
            page-break-inside: avoid;
        }

        .status {
            display: inline-block;
            padding: 4px 8px;
            border-radius: 5px;
            font-size: 12px;
            font-weight: bold;
            margin: 6px 0 12px;
        }

        .evidence {
            background: #f8fafc;
            border-left: 4px solid #9ca3af;
            padding: 12px;
            margin-top: 12px;
        }

        .page {
            font-size: 12px;
            margin-left: 8px;
            color: #4b5563;
        }

        .question {
            margin-top: 14px;
        }

        .pressure {
            border: 1px solid #e5d5b5;
            border-radius: 8px;
            padding: 12px;
            margin: 10px 0;
            background: #fffaf0;
        }

        .pressure span {
            margin-left: 8px;
            font-style: italic;
        }

        .helper {
            color: #4b5563;
        }

        footer {
            margin-top: 40px;
            padding-top: 16px;
            border-top: 1px solid #d1d5db;
            font-size: 13px;
            color: #4b5563;
        }
        
        .receipt-actions {
    display: flex;
    gap: 10px;
    margin-bottom: 20px;
}

.print-button,
.pdf-button {
    padding: 10px 16px;
    border: none;
    border-radius: 6px;
    color: white;
    font-weight: bold;
    cursor: pointer;
}

.print-button {
    background: #111827;
}

.pdf-button {
    background: #374151;
}

@media print {
    .receipt-actions {
        display: none;
    }

@media print {
    .print-button {
        display: none;
    }
        @media print {
            body {
                margin: 20px;
            }

            .claim {
                page-break-inside: avoid;
            }
        }
    </style>
</head>

<body>

    ${includeActions ? `
<div class="receipt-actions">
    <button
        class="print-button"
        onclick="window.print()"
    >
        Print Receipt
    </button>

    <button
        class="pdf-button"
        onclick="window.print()"
    >
        Save as PDF
    </button>
</div>
` : ""}

    <h1>VittNazar</h1>
    <p class="subtitle">
        Promise-to-Term Verification
    </p>

    <div class="receipt-id">
        <strong>Receipt ID:</strong>
        ${escapeHtml(receipt.receipt_id)}
        <br>
        <strong>Created:</strong>
        ${escapeHtml(receipt.created_at)}
    </div>

    <div class="summary">
    ${documentHtml}
        <div class="summary-box">
            <strong>${counts.total_claims}</strong><br>
            Total
        </div>

        <div class="summary-box">
            <strong>${counts.supported}</strong><br>
            Supported
        </div>

        <div class="summary-box">
            <strong>${counts.partially_supported || 0}</strong><br>
            Partial
        </div>

        <div class="summary-box">
            <strong>${counts.contradicted}</strong><br>
            Conflicts
        </div>

        <div class="summary-box">
            <strong>${counts.not_found}</strong><br>
            Needs review
        </div>
    </div>

    ${pressureHtml}

    <section>
        <h2>Promise Receipt</h2>
        ${claimsHtml}
    </section>

    <footer id="footer-text">
    VittNazar does not determine whether a seller is fraudulent
    or whether an investment is suitable. It compares supplied
    claims with supplied documentation and highlights information
    that requires independent verification.
</footer>

</body>
</html>
`;
return html;
}

function printReceipt(receipt) {
    const receiptWindow = window.open(
        "",
        "_blank"
    );

    if (!receiptWindow) {
        alert("Please allow pop-ups to print the receipt.");
        return;
    }

    const receiptHtml = buildReceiptHtml(
    receipt,
    false
);

    receiptWindow.document.open();
    receiptWindow.document.write(receiptHtml);
    receiptWindow.document.close();

    receiptWindow.onload = () => {
        receiptWindow.focus();
        receiptWindow.print();
    };
}


async function saveReceiptAsPdf(receipt) {
    try {
        savePdfButton.disabled = true;
        savePdfButton.textContent = "Creating PDF...";

        const response = await fetch(
            "/api/download-receipt",
            {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    receipt: receipt
                })
            }
        );

        if (!response.ok) {
            const data = await response.json();
            throw new Error(
                data.error || "PDF creation failed."
            );
        }

        const blob = await response.blob();

        const url = URL.createObjectURL(blob);

        const link = document.createElement("a");

        link.href = url;
        link.download =
            `VittNazar-${receipt.receipt_id}.pdf`;

        document.body.appendChild(link);

        link.click();

        document.body.removeChild(link);

        URL.revokeObjectURL(url);

    } catch (error) {
        alert(
            `Unable to create PDF: ${error.message}`
        );

    } finally {
        savePdfButton.disabled = false;
        savePdfButton.textContent = "Save as PDF";
    }
}

async function lookupReceipt() {
    const receiptIdValue =
        receiptIdInput.value.trim();

    lookupStatus.textContent = "";

    if (!receiptIdValue) {
        lookupStatus.textContent =
            "Please enter a Receipt ID.";

        return;
    }

    lookupReceiptButton.disabled = true;
    lookupReceiptButton.textContent = "Retrieving...";

    try {
        const response = await fetch(
            `/api/receipt?id=${encodeURIComponent(
                receiptIdValue
            )}`
        );

        const data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error || "Receipt retrieval failed."
            );
        }

        displayReceipt(data.receipt);

        lookupStatus.textContent =
    languageHiButton.classList.contains("active")
        ? "Receipt सफलतापूर्वक प्राप्त हो गई।"
        : "Receipt retrieved successfully.";

    } catch (error) {
    lookupStatus.textContent =
    languageHiButton.classList.contains("active")
        ? "Receipt नहीं मिली।"
        : error.message;

    // Clear the previously displayed receipt.
    resultsSection.classList.add("hidden");

    receiptId.textContent = "";

    summary.innerHTML = "";

    resultItems.innerHTML = "";

    pressureItems.innerHTML = "";

    pressureSection.classList.add("hidden");

    printReceiptButton.classList.add("hidden");

    savePdfButton.classList.add("hidden");

    copyReceiptIdButton.classList.add("hidden");

} finally {
    lookupReceiptButton.disabled = false;

    if (languageHiButton.classList.contains("active")) {
        lookupReceiptButton.textContent =
            "Receipt प्राप्त करें";
    } else {
        lookupReceiptButton.textContent =
            "Retrieve Receipt";
    }
}
}

async function copyReceiptId(receiptIdValue) {
    try {
        await navigator.clipboard.writeText(
            receiptIdValue
        );

        copyReceiptIdButton.textContent =
            "Copied!";

        setTimeout(() => {
            copyReceiptIdButton.textContent =
                "Copy ID";
        }, 1500);

    } catch (error) {
        copyReceiptIdButton.textContent =
            "Copy failed";

        setTimeout(() => {
            copyReceiptIdButton.textContent =
                "Copy ID";
        }, 1500);
    }
}

function setLanguage(language) {
    localStorage.setItem(
    "vittnazar-language",
    language
);
    if (language === "hi") {
        tagline.textContent =
            "वित्तीय वादे और शर्तों की जाँच";

        heroTitle.textContent =
            "वादा किए जाने से पहले समझें कि आपको क्या बताया गया है।";

        heroDescription.textContent =
            "वित्तीय बिक्री संदेश की तुलना आधिकारिक उत्पाद दस्तावेज़ से करें और देखें कि कौन से दावे समर्थित हैं, अधूरे हैं या दस्तावेज़ से मेल नहीं खाते।";

        salesTitle.textContent =
            "1. बिक्री संदेश";

        salesHelper.textContent =
            "संदेश, ईमेल या बिक्री विवरण यहाँ पेस्ट करें।";

        pitchInput.placeholder =
            "उदाहरण: 12% गारंटीड रिटर्न, कोई शुल्क नहीं। कभी भी पैसा निकालें।";

        documentTitle.textContent =
            "2. आधिकारिक दस्तावेज़";

        documentHelper.textContent =
            "आधिकारिक उत्पाद PDF अपलोड करें या संबंधित दस्तावेज़ का पाठ पेस्ट करें।";

        extractButton.textContent =
            "PDF निकालें";

        documentInput.placeholder =
    "निकाली गई PDF का पाठ यहाँ दिखाई देगा, या संबंधित दस्तावेज़ का पाठ स्वयं पेस्ट करें।";

        analyzeButton.textContent =
            "VittNazar से जाँच करें";

        lookupTitle.textContent =
            "Promise Receipt प्राप्त करें";

        lookupHelper.textContent =
            "पहले से सुरक्षित Receipt ID दर्ज करें।";

        lookupReceiptButton.textContent =
            "Receipt प्राप्त करें";

        receiptIdInput.placeholder =
    "उदाहरण: VN-20261003-120404";

        footerText.textContent =
    "VittNazar यह तय नहीं करता कि कोई विक्रेता धोखाधड़ी कर रहा है या कोई निवेश आपके लिए उपयुक्त है। यह दिए गए दावों की दिए गए दस्तावेज़ों से तुलना करता है और उन जानकारी को उजागर करता है जिनकी स्वतंत्र रूप से जाँच आवश्यक है।";

        receiptTitle.textContent =
    "Promise Receipt";

pressureTitle.textContent =
    "दबाव के संकेत";

pressureHelper.textContent =
    "ये बिक्री संदेश में पाए गए मनाने या दबाव डालने वाले पैटर्न हैं। ये गलत काम का प्रमाण नहीं हैं।";

        copyReceiptIdButton.textContent =
    "ID कॉपी करें";

printReceiptButton.textContent =
    "रसीद प्रिंट करें";

savePdfButton.textContent =
    "PDF के रूप में सहेजें";

    receiptTitle.textContent =
    "वादा रसीद";

documentMetadata.querySelector("h3").textContent =
    "सत्यापित दस्तावेज़";

        languageHiButton.classList.add(
            "active"
        );

        languageEnButton.classList.remove(
    "active"
);

if (currentReceipt) {
    displayReceipt(currentReceipt);
}

return;
    }

    tagline.textContent =
        "Promise-to-Term Verification";

    heroTitle.textContent =
        "Know what was promised before you commit.";

    heroDescription.textContent =
        "Compare a financial sales pitch with the official product documentation and identify claims that are supported, incomplete, or conflict with the supplied terms.";

    salesTitle.textContent =
        "1. Sales Pitch";

    salesHelper.textContent =
        "Paste the message, email, or sales statement.";

    pitchInput.placeholder =
        "Example: Guaranteed 12% return with zero charges. Withdraw anytime.";

    documentTitle.textContent =
        "2. Official Document";

    documentHelper.textContent =
        "Upload the official product PDF or paste its relevant text.";

    extractButton.textContent =
        "Extract PDF";

    documentInput.placeholder =
    "Extracted PDF text will appear here, or paste the relevant document text manually.";

    analyzeButton.textContent =
        "Analyze with VittNazar";

    lookupTitle.textContent =
        "Retrieve a Promise Receipt";

    lookupHelper.textContent =
        "Enter a Receipt ID to reopen a previously saved receipt.";

    lookupReceiptButton.textContent =
        "Retrieve Receipt";
    
    receiptIdInput.placeholder =
    "Example: VN-20261003-120404";

    footerText.textContent =
    "VittNazar does not determine whether a seller is fraudulent or whether an investment is suitable. It compares supplied claims with supplied documentation and highlights information that requires independent verification.";

    receiptTitle.textContent =
    "Promise Receipt";

pressureTitle.textContent =
    "Pressure Signals";

pressureHelper.textContent =
    "These are persuasion patterns detected in the sales message. They are not proof of wrongdoing.";

    copyReceiptIdButton.textContent =
    "Copy ID";

printReceiptButton.textContent =
    "Print Receipt";

savePdfButton.textContent =
    "Save as PDF";

    receiptTitle.textContent =
    "Promise Receipt";

documentMetadata.querySelector("h3").textContent =
    "Verified Document";
    
    languageEnButton.classList.add(
        "active"
    );

    languageHiButton.classList.remove(
        "active"
    );

    if (currentReceipt) {
    displayReceipt(currentReceipt);
}
}

setLanguage(
    localStorage.getItem("vittnazar-language") || "en"
);