/**
 * Render network graph with visual distinction
 * Actual flows: Solid, vibrant
 * Predicted flows: Lighter, semi-transparent, dashed
 */

function renderNetworkGraph(containerId, data, state = 'current') {
    const svg = d3.select(containerId);
    const width = svg.node().getBoundingClientRect().width;
    const height = 600;
    
    // Color scheme based on state
    const colors = state === 'current' ? ACTUAL_COLORS : PREDICTED_COLORS;
    
    // Create force simulation
    const simulation = d3.forceSimulation(data.nodes)
        .force("link", d3.forceLink(data.links).id(d => d.id).distance(120))
        .force("charge", d3.forceManyBody().strength(-400))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(40));
    
    // Draw links
    const link = svg.append("g")
        .selectAll("line")
        .data(data.links)
        .enter().append("line")
        .attr("class", d => d.predicted ? "link-predicted" : "link-actual")
        .attr("stroke", d => {
            if (d.markov_probability) {
                // Markov prediction - color by confidence
                if (d.markov_probability > 0.7) return colors.high_confidence;
                if (d.markov_probability > 0.4) return colors.medium_confidence;
                return colors.low_confidence;
            }
            return d.predicted ? colors.predicted_flow : colors.actual_flow;
        })
        .attr("stroke-width", d => Math.sqrt(d.value || 1))
        .attr("stroke-opacity", d => {
            if (d.markov_probability) {
                return d.markov_probability; // Opacity = confidence
            }
            return d.predicted ? 0.4 : 0.8;
        })
        .attr("stroke-dasharray", d => {
            // Actual: solid
            // Predicted: dashed
            // Markov: dotted
            if (d.markov_probability) return "2,2"; // Dotted
            return d.predicted ? "5,5" : "0"; // Dashed or solid
        });
    
    // Draw nodes
    const node = svg.append("g")
        .selectAll("circle")
        .data(data.nodes)
        .enter().append("circle")
        .attr("r", d => d.size || 10)
        .attr("fill", d => colors[d.zone] || colors.UNASSIGNED)
        .attr("stroke", "#fff")
        .attr("stroke-width", d => d.predicted ? 3 : 2)
        .attr("stroke-dasharray", d => d.predicted ? "3,3" : "0")
        .attr("opacity", d => d.predicted ? 0.7 : 1.0)
        .on("click", showNodeDetails)
        .call(d3.drag()
            .on("start", dragstarted)
            .on("drag", dragged)
            .on("end", dragended));
    
    // Add labels
    const labels = svg.append("g")
        .selectAll("text")
        .data(data.nodes)
        .enter().append("text")
        .attr("class", "node-label")
        .attr("font-size", "10px")
        .attr("fill", d => d.predicted ? "#ccc" : "#fff")
        .text(d => d.label);
    
    // Update positions on simulation tick
    simulation.on("tick", () => {
        link
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        node
            .attr("cx", d => d.x)
            .attr("cy", d => d.y);
        
        labels
            .attr("x", d => d.x + 12)
            .attr("y", d => d.y + 4);
    });
}

// Add legend
function addLegend(containerId) {
    const legend = d3.select(containerId)
        .append("div")
        .attr("class", "legend-container");
    
    legend.append("h3").text("Legend");
    
    // Actual flows
    legend.append("div")
        .attr("class", "legend-item")
        .html(`
            <svg width="40" height="4">
                <line x1="0" y1="2" x2="40" y2="2" 
                      stroke="#4CAF50" stroke-width="3" opacity="0.8"/>
            </svg>
            <span>Actual Flow (Current State)</span>
        `);
    
    // Predicted flows
    legend.append("div")
        .attr("class", "legend-item")
        .html(`
            <svg width="40" height="4">
                <line x1="0" y1="2" x2="40" y2="2" 
                      stroke="#81C784" stroke-width="3" opacity="0.4" 
                      stroke-dasharray="5,5"/>
            </svg>
            <span>Predicted Flow (Future State)</span>
        `);
    
    // Markov predictions
    legend.append("div")
        .attr("class", "legend-item")
        .html(`
            <svg width="40" height="4">
                <line x1="0" y1="2" x2="40" y2="2" 
                      stroke="#81C784" stroke-width="3" opacity="0.8" 
                      stroke-dasharray="2,2"/>
            </svg>
            <span>Markov Prediction (High Confidence >70%)</span>
        `);
    
    legend.append("div")
        .attr("class", "legend-item")
        .html(`
            <svg width="40" height="4">
                <line x1="0" y1="2" x2="40" y2="2" 
                      stroke="#FFB74D" stroke-width="3" opacity="0.5" 
                      stroke-dasharray="2,2"/>
            </svg>
            <span>Markov Prediction (Medium 40-70%)</span>
        `);
    
    legend.append("div")
        .attr("class", "legend-item")
        .html(`
            <svg width="40" height="4">
                <line x1="0" y1="2" x2="40" y2="2" 
                      stroke="#E57373" stroke-width="3" opacity="0.3" 
                      stroke-dasharray="2,2"/>
            </svg>
            <span>Markov Prediction (Low <40%)</span>
        `);
}