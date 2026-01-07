const API_URL = 'https://review-predictor-using-llm.onrender.com/api';

// Chart.js instance
let ratingsChart = null;

// Utility to fetch data
async function fetchData(endpoint) {
    try {
        const res = await fetch(`${API_URL}${endpoint}`);
        if (!res.ok) throw new Error('API Error');
        return await res.json();
    } catch (e) {
        console.error(`Failed to fetch ${endpoint}`, e);
        return null;
    }
}

function formatDate(dateString) {
    return new Date(dateString).toLocaleString();
}

function createStars(count) {
    return '★'.repeat(count) + '☆'.repeat(5 - count);
}

// Initialize or update Chart.js ratings chart
async function updateRatingsChart() {
    const ratingsData = await fetchData('/analytics/ratings');

    if (!ratingsData || !ratingsData.ratings) return;

    // Count occurrences of each rating (handle 0 ratings as invalid)
    const ratingCounts = [0, 0, 0, 0, 0]; // For ratings 1-5
    ratingsData.ratings.forEach(rating => {
        if (rating >= 1 && rating <= 5) {
            ratingCounts[rating - 1]++;
        }
    });

    const ctx = document.getElementById('ratingsChart');
    const totalReviews = ratingsData.total_reviews || 0;

    if (ratingsChart) {
        // Update existing chart with smooth animation
        ratingsChart.data.datasets[0].data = ratingCounts;
        ratingsChart.options.plugins.title.text = `Average: ${ratingsData.average_rating?.toFixed(1) || 'N/A'} / 5.0 | Total Reviews: ${totalReviews}`;
        ratingsChart.update('active');
    } else {
        // Create gradient backgrounds for bars
        const createGradient = (ctx, color1, color2) => {
            const gradient = ctx.createLinearGradient(0, 0, 0, 400);
            gradient.addColorStop(0, color1);
            gradient.addColorStop(1, color2);
            return gradient;
        };

        // Create new chart with enhanced styling
        ratingsChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: ['1 Star', '2 Stars', '3 Stars', '4 Stars', '5 Stars'],
                datasets: [{
                    label: 'Reviews',
                    data: ratingCounts,
                    backgroundColor: [
                        'rgba(239, 68, 68, 0.8)',   // Red for 1 star
                        'rgba(251, 146, 60, 0.8)',  // Orange for 2 stars
                        'rgba(251, 191, 36, 0.8)',  // Yellow for 3 stars
                        'rgba(163, 230, 53, 0.8)',  // Light green for 4 stars
                        'rgba(16, 185, 129, 0.8)'   // Green for 5 stars
                    ],
                    borderColor: [
                        'rgb(239, 68, 68)',
                        'rgb(251, 146, 60)',
                        'rgb(251, 191, 36)',
                        'rgb(163, 230, 53)',
                        'rgb(16, 185, 129)'
                    ],
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                animation: {
                    duration: 1000,
                    easing: 'easeInOutQuart'
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: `Average: ${ratingsData.average_rating?.toFixed(1) || 'N/A'} / 5.0 | Total Reviews: ${totalReviews}`,
                        color: '#f8fafc',
                        padding: {
                            top: 10,
                            bottom: 20
                        },
                        font: {
                            size: 16,
                            weight: '600',
                            family: 'Inter'
                        }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        titleColor: '#f8fafc',
                        bodyColor: '#94a3b8',
                        borderColor: 'rgba(99, 102, 241, 0.5)',
                        borderWidth: 1,
                        padding: 12,
                        displayColors: true,
                        callbacks: {
                            title: function (context) {
                                return context[0].label;
                            },
                            label: function (context) {
                                const count = context.parsed.y;
                                const percentage = totalReviews > 0
                                    ? ((count / totalReviews) * 100).toFixed(1)
                                    : 0;
                                return [
                                    `Reviews: ${count}`,
                                    `Percentage: ${percentage}%`
                                ];
                            }
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            color: '#94a3b8',
                            stepSize: 1,
                            font: {
                                size: 12,
                                family: 'Inter'
                            },
                            padding: 8
                        },
                        grid: {
                            color: 'rgba(148, 163, 184, 0.08)',
                            drawBorder: false
                        },
                        border: {
                            display: false
                        },
                        title: {
                            display: true,
                            text: 'Number of Reviews',
                            color: '#94a3b8',
                            font: {
                                size: 12,
                                weight: '500'
                            }
                        }
                    },
                    x: {
                        ticks: {
                            color: '#f8fafc',
                            font: {
                                size: 18,
                                family: 'Inter'
                            },
                            padding: 10
                        },
                        grid: {
                            display: false,
                            drawBorder: false
                        },
                        border: {
                            display: false
                        }
                    }
                }
            }
        });
    }
}

async function renderDashboard() {
    const refreshBtn = document.getElementById('refreshBtn');
    refreshBtn.classList.add('loading');

    // Fetch in parallel
    const [reviewsData, sentimentData, ratingsData] = await Promise.all([
        fetchData('/admin/reviews'),
        fetchData('/analytics/sentiment'),
        fetchData('/analytics/ratings')
    ]);

    // Update time
    document.getElementById('lastUpdated').textContent = `Updated: ${new Date().toLocaleTimeString()}`;

    // Update Stats
    if (sentimentData) {
        document.getElementById('sentimentScore').textContent = sentimentData.sentiment_score + '/100';
        document.getElementById('sentimentLabel').textContent = sentimentData.overall_sentiment;
    }

    // Update Average Rating
    if (ratingsData) {
        const avgRating = ratingsData.average_rating?.toFixed(1) || '-';
        document.getElementById('averageRating').textContent = avgRating;
    }

    // Render Reviews
    if (reviewsData && reviewsData.reviews) {
        document.getElementById('totalReviews').textContent = reviewsData.total_count || reviewsData.reviews.length;

        const list = document.getElementById('reviewsList');
        list.innerHTML = '';

        if (reviewsData.reviews.length === 0) {
            list.innerHTML = '<div style="text-align: center; padding: 2rem;">No reviews yet.</div>';
        } else {
            reviewsData.reviews.forEach(review => {
                const item = document.createElement('div');
                item.className = 'glass-panel review-card';
                item.style.background = 'rgba(15, 23, 42, 0.3)';
                item.innerHTML = `
                    <div class="review-header">
                        <div class="review-rating" style="font-size: 1.2rem;">
                            ${createStars(review.rating)} 
                            <span style="color:white; font-size:0.9rem; margin-left:8px; font-weight:normal;">${review.rating}/5</span>
                        </div>
                        <div style="font-size: 0.8rem; color: var(--text-secondary);">
                            ${formatDate(review.created_at)}
                        </div>
                    </div>
                    <div style="margin-bottom: 1rem; font-size: 1.1rem; color: white;">"${review.review_text || ''}"</div>
                    
                    ${review.ai_summary ? `
                    <div class="review-ai-section">
                        <div style="color: var(--accent-color); font-weight: 600; margin-bottom: 4px;">AI Summary</div>
                        <p style="margin-bottom: 8px;">${review.ai_summary}</p>
                        
                        ${review.ai_recommended_action ? `
                        <div style="color: var(--success-color); font-weight: 600; margin-bottom: 4px; margin-top: 12px;">Recommended Action</div>
                        <p>${review.ai_recommended_action}</p>
                        ` : ''}
                    </div>
                    ` : ''}
                `;
                list.appendChild(item);
            });
        }
    }

    // Update chart
    await updateRatingsChart();

    refreshBtn.classList.remove('loading');
}

// Modal functions
function showModal(title, content) {
    const modal = document.getElementById('analyticsModal');
    const modalBody = document.getElementById('modalBody');

    modalBody.innerHTML = `<h2>${title}</h2>${content}`;
    modal.classList.add('active');
}

function closeModal() {
    const modal = document.getElementById('analyticsModal');
    modal.classList.remove('active');
}

// Analytics button handlers
async function showSentimentAnalysis() {
    const btn = document.getElementById('sentimentBtn');
    btn.classList.add('loading');

    const data = await fetchData('/analytics/sentiment');

    if (data) {
        const content = `
            <div style="margin-top: 1.5rem;">
                <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 1rem;">
                    <h3 style="color: var(--accent-color);">Overall Sentiment</h3>
                    <p style="font-size: 1.5rem; font-weight: 700; margin: 0.5rem 0;">
                        ${data.overall_sentiment}
                    </p>
                    <p style="color: var(--text-secondary);">
                        Score: ${data.sentiment_score}/100 | Reviews Analyzed: ${data.total_reviews_analyzed}
                    </p>
                </div>

                <div class="glass-panel" style="padding: 1.5rem; margin-bottom: 1rem;">
                    <h3 style="color: var(--accent-color);">Key Themes</h3>
                    <div style="display: flex; flex-wrap: wrap; gap: 0.5rem; margin-top: 1rem;">
                        ${data.key_themes?.map(theme => `<span class="tag">${theme}</span>`).join('') || 'No themes detected'}
                    </div>
                </div>

                <div class="glass-panel" style="padding: 1.5rem;">
                    <h3 style="color: var(--accent-color);">Admin Insight</h3>
                    <p style="margin-top: 1rem; line-height: 1.8;">
                        ${data.admin_insight || 'No insights available'}
                    </p>
                </div>
            </div>
        `;
        showModal('📊 Sentiment Analysis', content);
    } else {
        alert('Failed to load sentiment analysis');
    }

    btn.classList.remove('loading');
}

async function showRecommendations() {
    const btn = document.getElementById('recommendationsBtn');
    btn.classList.add('loading');

    const data = await fetchData('/analytics/recommendations');

    if (data) {
        let content = `
            <div style="margin-top: 1.5rem;">
                <p style="color: var(--text-secondary); margin-bottom: 1.5rem;">
                    Analyzed ${data.total_recommendations_analyzed || 0} recommendations
                </p>
        `;

        // Priority Recommendations
        if (data.priority_recommendations && data.priority_recommendations.length > 0) {
            content += `
                <h3 style="color: var(--accent-color); margin-bottom: 1rem;">Priority Actions</h3>
            `;
            data.priority_recommendations.forEach(rec => {
                const priority = rec.priority?.toLowerCase() || 'medium';
                content += `
                    <div class="recommendation-card priority-${priority}">
                        <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 0.5rem;">
                            <strong style="color: var(--text-primary);">${rec.action}</strong>
                            <span class="priority-badge ${priority}">${rec.priority || 'Medium'}</span>
                        </div>
                        <p style="color: var(--text-secondary); font-size: 0.9rem;">
                            ${rec.reason || ''}
                        </p>
                    </div>
                `;
            });
        }

        // Quick Wins
        if (data.quick_wins && data.quick_wins.length > 0) {
            content += `
                <h3 style="color: var(--success-color); margin: 1.5rem 0 1rem;">⚡ Quick Wins</h3>
                <ul style="list-style: none; padding: 0;">
            `;
            data.quick_wins.forEach(win => {
                content += `<li style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">✓ ${win}</li>`;
            });
            content += `</ul>`;
        }

        // Long-term Improvements
        if (data.long_term_improvements && data.long_term_improvements.length > 0) {
            content += `
                <h3 style="color: #fbbf24; margin: 1.5rem 0 1rem;">🎯 Long-term Improvements</h3>
                <ul style="list-style: none; padding: 0;">
            `;
            data.long_term_improvements.forEach(improvement => {
                content += `<li style="padding: 0.5rem 0; border-bottom: 1px solid rgba(255,255,255,0.1);">→ ${improvement}</li>`;
            });
            content += `</ul>`;
        }

        content += `</div>`;
        showModal('💡 Priority Recommendations', content);
    } else {
        alert('Failed to load recommendations');
    }

    btn.classList.remove('loading');
}

// Event Listeners
document.getElementById('refreshBtn').addEventListener('click', renderDashboard);
document.getElementById('sentimentBtn').addEventListener('click', showSentimentAnalysis);
document.getElementById('recommendationsBtn').addEventListener('click', showRecommendations);
document.getElementById('modalClose').addEventListener('click', closeModal);

// Close modal when clicking outside
document.getElementById('analyticsModal').addEventListener('click', (e) => {
    if (e.target.id === 'analyticsModal') {
        closeModal();
    }
});

// Initial Load
renderDashboard();

// Auto Refresh every 5 seconds (as requested)
setInterval(renderDashboard, 5000);
