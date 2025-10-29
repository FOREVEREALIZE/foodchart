// Render Timed Points
export function renderTimedPoints(pointsTimedG, timedPointData, x, y, showTooltip, hideTooltip, formatName, timedData) {
    pointsTimedG.selectAll('circle')
        .data(timedPointData)
        .join('circle')
        .attr('cx', d => x(d.percent))
        .attr('cy', d => y(d.fixed))
        .attr('r', 4)
        .attr('opacity', d => (d.tick || 0) === (d.maxTicks || -1) ? 1 : 0.05)
        .attr('fill', 'crimson')
        .on('mousemove', (event, d) => {
            if ((d.tick || 0) !== (d.maxTicks || -1)) return;
            
            const matches = timedData.filter(item => item.healing.base.percent === d.percent);
            const formattedMatches = matches.map(formatName).join('<br />');
            const maxFixed = matches[0].healing.steps
                .sort((a, b) => b.tick - a.tick)[0].fixed.toFixed(0);

            showTooltip(event,
                `<strong>${matches[0].healing.base.percent.toFixed(0)}% + ${maxFixed}</strong><br />${formattedMatches}`
            );
        })
        .on('mouseleave', hideTooltip);
}