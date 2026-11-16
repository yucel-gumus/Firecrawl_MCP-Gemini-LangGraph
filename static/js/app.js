let currentResultData = null;
        let currentUrl = '';
        let currentDurations = {};
        let currentStats = {};

        function escapeHtml(val) {
            return String(val ?? '')
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/"/g, '&quot;')
                .replace(/'/g, '&#39;');
        }

        function setUrl(url) {
            document.getElementById('url-input').value = url;
        }

        function showToast(message) {
            const toast = document.getElementById('app-toast');
            toast.textContent = message;
            toast.style.display = 'block';
            setTimeout(() => {
                toast.style.display = 'none';
            }, 2500);
        }

        function switchTab(tabId, btnEl) {
            document.querySelectorAll('.tab-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(pane => pane.classList.remove('active'));

            const targetBtn = btnEl || (typeof event !== 'undefined' && event.target ? event.target : null);
            if (targetBtn) {
                targetBtn.classList.add('active');
            }
            const targetPane = document.getElementById(`tab-pane-${tabId}`);
            if (targetPane) {
                targetPane.classList.add('active');
            }
        }

        function copyJsonOutput() {
            if (!currentResultData) return;
            navigator.clipboard.writeText(JSON.stringify(currentResultData, null, 2)).then(() => {
                showToast('JSON çıktısı panoya kopyalandı.');
            });
        }

        function copyMarkdownOutput() {
            if (!currentResultData) return;
            let md = `# Web İçerik Analizi Raporu\n\n**Kaynak URL:** ${currentUrl}\n\n## 1. Yönetici Özeti\n${currentResultData.executive_summary || ''}\n\n## 2. Detaylı Konu Kırılımları\n`;
            (currentResultData.topics || []).forEach(t => {
                md += `\n### ${t.topic}\n${t.details}\n`;
                (t.key_points || []).forEach(p => { md += `- ${p}\n`; });
            });
            md += `\n## 3. Stratejik Bulgular\n`;
            (currentResultData.key_findings || []).forEach(f => { md += `- ${f}\n`; });
            md += `\n## 4. Eylem Maddeleri\n`;
            (currentResultData.actionable_takeaways || []).forEach(a => { md += `- ${a}\n`; });

            navigator.clipboard.writeText(md).then(() => {
                showToast('Markdown formatında panoya kopyalandı.');
            });
        }

        // --- Executive PDF Generation ---
        function generatePdfReport() {
            if (!currentResultData) {
                showToast('Önce bir URL analiz etmelisiniz.');
                return;
            }

            const pdfBtn = document.getElementById('btn-pdf-export');
            const originalText = pdfBtn.innerHTML;
            pdfBtn.innerHTML = '<span>PDF Hazırlanıyor...</span>';
            pdfBtn.disabled = true;

            const now = new Date();
            document.getElementById('pdf-report-id').textContent = 'R-' + Math.floor(100000 + Math.random() * 900000);
            document.getElementById('pdf-date').textContent = now.toLocaleDateString('tr-TR') + ' ' + now.toLocaleTimeString('tr-TR');
            document.getElementById('pdf-url-text').textContent = currentUrl;
            document.getElementById('pdf-perf-text').textContent = `Toplam Süre: ${(currentDurations.total_seconds || 0).toFixed(2)}s | Kazınan Boyut: ${(currentStats.scraped_content_length || 0).toLocaleString()} karakter`;

            // Exec text
            document.getElementById('pdf-exec-text').textContent = currentResultData.executive_summary || 'Özet bulunamadı.';

            // Topics
            const pdfTopics = document.getElementById('pdf-topics-container');
            pdfTopics.innerHTML = '';
            (currentResultData.topics || []).forEach(t => {
                const box = document.createElement('div');
                box.className = 'pdf-topic-card-print';
                let subBullets = '';
                (t.key_points || []).forEach(bp => {
                    subBullets += `<li>${escapeHtml(bp)}</li>`;
                });
                box.innerHTML = `
                    <div class="pdf-topic-name-print">${escapeHtml(t.topic || 'Konu')}</div>
                    <div class="pdf-topic-desc-print">${escapeHtml(t.details || '')}</div>
                    <ul class="pdf-topic-bullets-print">${subBullets}</ul>
                `;
                pdfTopics.appendChild(box);
            });

            // Stats
            const pdfStatsTbody = document.getElementById('pdf-stats-tbody');
            pdfStatsTbody.innerHTML = '';
            (currentResultData.statistics || []).forEach(s => {
                const tr = document.createElement('tr');
                if (typeof s === 'object' && s !== null) {
                    tr.innerHTML = `
                        <td style="font-weight: 600;">${escapeHtml(s.metric || '')}</td>
                        <td style="font-weight: 700; color: #0f172a;">${escapeHtml(s.value || '')}</td>
                        <td>${escapeHtml(s.context || '')}</td>
                    `;
                } else {
                    tr.innerHTML = `<td colspan="3">${escapeHtml(s)}</td>`;
                }
                pdfStatsTbody.appendChild(tr);
            });
            if (!currentResultData.statistics || currentResultData.statistics.length === 0) {
                pdfStatsTbody.innerHTML = '<tr><td colspan="3" style="color: #94a3b8;">Metinde sayısal veri tespit edilmedi.</td></tr>';
            }

            // Findings
            const pdfFindings = document.getElementById('pdf-findings-list');
            pdfFindings.innerHTML = '';
            (currentResultData.key_findings || []).forEach(f => {
                const li = document.createElement('li');
                li.textContent = f;
                pdfFindings.appendChild(li);
            });

            // Takeaways
            const pdfTakeaways = document.getElementById('pdf-takeaways-list');
            pdfTakeaways.innerHTML = '';
            (currentResultData.actionable_takeaways || []).forEach(a => {
                const li = document.createElement('li');
                li.textContent = a;
                pdfTakeaways.appendChild(li);
            });

            // Entities
            const pdfEntities = document.getElementById('pdf-entities-container');
            if (pdfEntities) {
                pdfEntities.innerHTML = '';
                (currentResultData.entities_and_technologies || []).forEach(e => {
                    const pill = document.createElement('span');
                    pill.className = 'pdf-entity-pill';
                    pill.textContent = e;
                    pdfEntities.appendChild(pill);
                });
                if (!currentResultData.entities_and_technologies || currentResultData.entities_and_technologies.length === 0) {
                    pdfEntities.innerHTML = '<span style="font-size: 9.5px; color: #94a3b8;">Belirli bir varlık listelenmedi.</span>';
                }
            }

            let domain = 'analiz_raporu';
            try {
                domain = new URL(currentUrl).hostname.replace('www.', '');
            } catch (e) { }
            const fileName = `Rapor_${domain}_${now.toISOString().slice(0, 10)}.pdf`;

            // Use native browser print for clean, full-width PDF output
            setTimeout(() => {
                window.print();
                showToast('PDF olarak kaydetmek için "Farklı Kaydet" seçin.');
                pdfBtn.innerHTML = originalText;
                pdfBtn.disabled = false;
            }, 200);
        }

        // --- Form Submit & Orchestration ---
        document.getElementById('intelligence-form').addEventListener('submit', async function (e) {
            e.preventDefault();
            const urlInput = document.getElementById('url-input');
            const submitBtn = document.getElementById('submit-btn');
            const loadingView = document.getElementById('loading-view');
            const emptyState = document.getElementById('empty-state-view');
            const resultsCanvas = document.getElementById('results-canvas');
            const errorBanner = document.getElementById('error-banner');

            const url = urlInput.value.trim();
            if (!url) return;
            currentUrl = url;

            errorBanner.style.display = 'none';
            emptyState.style.display = 'none';
            resultsCanvas.style.display = 'none';
            loadingView.style.display = 'block';
            submitBtn.disabled = true;

            try {
                const response = await fetch('/summarize', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ url: url })
                });

                const data = await response.json();

                if (!response.ok || data.success === false) {
                    throw new Error(data.error || `Sunucu hatası (${response.status})`);
                }

                currentResultData = data.summary || data;
                currentDurations = data.durations || {};
                currentStats = data.content_stats || {};

                // Target URL & Metrics
                document.getElementById('display-target-url').textContent = url;
                document.getElementById('metric-total-time').textContent = (currentDurations.total_seconds || 0).toFixed(2) + 's';
                document.getElementById('metric-scrape-time').textContent = (currentDurations.scraping_seconds || 0).toFixed(2) + 's';
                document.getElementById('metric-llm-time').textContent = (currentDurations.llm_processing_seconds || 0).toFixed(2) + 's';
                document.getElementById('metric-content-size').textContent = (currentStats.scraped_content_length || 0).toLocaleString() + ' kar.';

                // 1. Executive Summary
                document.getElementById('view-exec-summary').textContent = currentResultData.executive_summary || 'Özet bilgisi bulunamadı.';

                // 2. Preview Findings & Actions (in Overview Tab)
                const previewFindings = document.getElementById('view-preview-findings');
                previewFindings.innerHTML = '';
                (currentResultData.key_findings || []).slice(0, 3).forEach(f => {
                    const li = document.createElement('li');
                    li.textContent = f;
                    previewFindings.appendChild(li);
                });

                const previewActions = document.getElementById('view-preview-actions');
                previewActions.innerHTML = '';
                (currentResultData.actionable_takeaways || []).slice(0, 3).forEach(a => {
                    const li = document.createElement('li');
                    li.textContent = a;
                    previewActions.appendChild(li);
                });

                // 3. Topics Stack
                const topicsContainer = document.getElementById('view-topics-container');
                topicsContainer.innerHTML = '';
                (currentResultData.topics || []).forEach(t => {
                    const card = document.createElement('div');
                    card.className = 'topic-article-box';
                    let subBullets = '';
                    (t.key_points || []).forEach(p => {
                        subBullets += `<li>${escapeHtml(p)}</li>`;
                    });
                    card.innerHTML = `
                        <div class="topic-article-name">${escapeHtml(t.topic || 'Konu')}</div>
                        <div class="topic-article-desc">${escapeHtml(t.details || '')}</div>
                        <ul class="topic-sub-points">${subBullets}</ul>
                    `;
                    topicsContainer.appendChild(card);
                });
                if (!currentResultData.topics || currentResultData.topics.length === 0) {
                    topicsContainer.innerHTML = '<p style="color: var(--text-muted);">Konu kırılımı bulunamadı.</p>';
                }

                // 4. Statistics Table
                const statsTbody = document.getElementById('view-stats-tbody');
                statsTbody.innerHTML = '';
                (currentResultData.statistics || []).forEach(s => {
                    const tr = document.createElement('tr');
                    if (typeof s === 'object' && s !== null) {
                        tr.innerHTML = `
                            <td style="font-weight: 600; color: #ffffff;">${escapeHtml(s.metric || 'Metrik')}</td>
                            <td class="metric-badge-col">${escapeHtml(s.value || '')}</td>
                            <td>${escapeHtml(s.context || '')}</td>
                        `;
                    } else {
                        tr.innerHTML = `<td colspan="3">${escapeHtml(s)}</td>`;
                    }
                    statsTbody.appendChild(tr);
                });
                if (!currentResultData.statistics || currentResultData.statistics.length === 0) {
                    statsTbody.innerHTML = '<tr><td colspan="3" style="color: var(--text-dim); padding: 14px;">Metinde somut istatistiki veri tespit edilmedi.</td></tr>';
                }

                // 5. Full Findings & Actions Tab
                const fullFindings = document.getElementById('view-full-findings');
                fullFindings.innerHTML = '';
                (currentResultData.key_findings || []).forEach(f => {
                    const li = document.createElement('li');
                    li.textContent = f;
                    fullFindings.appendChild(li);
                });

                const fullActions = document.getElementById('view-full-actions');
                fullActions.innerHTML = '';
                (currentResultData.actionable_takeaways || []).forEach(a => {
                    const li = document.createElement('li');
                    li.textContent = a;
                    fullActions.appendChild(li);
                });

                // 6. Entities
                const entitiesContainer = document.getElementById('view-entities-container');
                entitiesContainer.innerHTML = '';
                (currentResultData.entities_and_technologies || []).forEach(e => {
                    const chip = document.createElement('span');
                    chip.className = 'entity-chip-item';
                    chip.textContent = e;
                    entitiesContainer.appendChild(chip);
                });

                // 7. Raw JSON
                document.getElementById('view-raw-json').textContent = JSON.stringify(currentResultData, null, 2);

                // Reveal Canvas
                loadingView.style.display = 'none';
                resultsCanvas.style.display = 'flex';

            } catch (err) {
                loadingView.style.display = 'none';
                emptyState.style.display = 'block';
                errorBanner.textContent = 'Hata: ' + err.message;
                errorBanner.style.display = 'block';
            } finally {
                submitBtn.disabled = false;
            }
        });