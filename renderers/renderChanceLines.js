import * as d3 from "https://cdn.jsdelivr.net/npm/d3@7/+esm";

export function renderChanceLines(chanceLineG, chanceData, x, y) {
    const lineGen = d3.line()
        .x(d => x(d.percent))
        .y(d => y(d.fixed));

    const chanceLineData = chanceData.map(v => {
        const outcomes = v.healing.outcomes.toSorted((a, b) => a.percent - b.percent);
        return outcomes;
    });

    chanceLineG.selectAll('path.connection-line')
        .data(chanceLineData)
        .join('path')
        .attr('class', 'connection-line')
        .attr('fill', 'none')
        .attr('stroke', 'coral')
        .attr('stroke-width', 2)
        .attr('opacity', 0.3)
        .attr('d', d => lineGen(d));
}