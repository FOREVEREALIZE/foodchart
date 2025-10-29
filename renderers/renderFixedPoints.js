// Render Fixed Points
export function renderFixedPoints(pointsG, fixedData, x, y, showTooltip, hideTooltip, formatName) {
    pointsG.selectAll('circle')
        .data(fixedData)
        .join('circle')
        .attr('cx', d => x(d.healing.percent))
        .attr('cy', d => y(d.healing.fixed))
        .attr('r', 4)
        .attr('fill', 'steelblue')
        .on('mousemove', (event, d) => {
            const matches = fixedData
                .filter(item => 
                    item.healing.percent === d.healing.percent && 
                    item.healing.fixed === d.healing.fixed
                )
                .map(formatName)
                .join('<br />');

            showTooltip(event, 
                `<strong>${d.healing.percent.toFixed(0)}% + ${d.healing.fixed}</strong><br />${matches}`
            );
        })
        .on('mouseleave', hideTooltip);
}