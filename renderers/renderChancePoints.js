// Render Chance Points
export function renderChancePoints(pointsChanceG, chancePointData, x, y, showTooltip, hideTooltip, formatName, chanceData) {
    pointsChanceG.selectAll('circle')
        .data(chancePointData)
        .join('circle')
        .attr('cx', d => x(d.percent))
        .attr('cy', d => y(d.fixed))
        .attr('r', 4)
        .attr('opacity', 0.75)
        .attr('fill', 'coral')
        .on('mousemove', (event, d) => {
            const matches = chanceData.filter(item => item.id === d.id);
            const formattedMatches = matches.map(formatName).join('<br />');
            const outcomes = matches[0].healing.outcomes;

            const minPercent = Math.min(...outcomes.map(v => v.percent));
            const minFixed = Math.min(...outcomes.map(v => v.fixed));
            const maxPercent = Math.max(...outcomes.map(v => v.percent));
            const maxFixed = Math.max(...outcomes.map(v => v.fixed));

            showTooltip(event,
                `<strong>${minPercent.toFixed(0)}~${maxPercent.toFixed(0)}% + ${minFixed.toFixed(0)}~${maxFixed.toFixed(0)}<br />${d.percent.toFixed(0)}% + ${d.fixed.toFixed(0)}</strong><br />${formattedMatches}`
            );
        })
        .on('mouseleave', hideTooltip);
}