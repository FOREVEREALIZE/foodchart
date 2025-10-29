// Render Revival Points
export function renderRevivalPoints(pointsRevivalG, revivalFixedData, x, y, showTooltip, hideTooltip, formatName) {
    pointsRevivalG.selectAll('circle')
        .data(revivalFixedData)
        .join('circle')
        .attr('cx', d => x(d.healing.percent))
        .attr('cy', d => y(d.healing.fixed))
        .attr('r', 4)
        .attr('fill', 'green')
        .on('mousemove', (event, d) => {
            const matches = revivalFixedData
                .filter(item => 
                    item.healing.percent === d.healing.percent && 
                    item.healing.fixed === d.healing.fixed
                )
                .map(formatName)
                .join('<br />');

            showTooltip(event, 
                `<strong>Revival: ${d.healing.percent.toFixed(0)}% + ${d.healing.fixed}</strong><br />${matches}`
            );
        })
        .on('mouseleave', hideTooltip);
}