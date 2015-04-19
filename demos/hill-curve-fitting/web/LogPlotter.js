// Copyright (c) 2015 MIT Probabilistic Computing Project.
//
// This file is part of Venture.
//
// Venture is free software: you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// Venture is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with Venture.  If not, see <http://www.gnu.org/licenses/>.

function Plotter(doc, svg, ns) {
	this.doc = doc;
	this.svg = svg;
	this.ns = ns;
	this.minX = -3;
	this.minY = 0.0;
	this.stepX = 1;
	this.stepY = 0.1;
	this.maxX = 3;
	this.maxY = 1.0;
	this.points = [];
	this.functions = [];
	this.gridElements = [];

	this.xSVGToGraph = function(x) {
        return Math.pow(10, x * (this.maxX - this.minX) / this.svg.width.baseVal.value + this.minX);
    }

    this.xGraphToSVG = function(x) {
        return (Math.log(x) / Math.LN10 - this.minX) * this.svg.width.baseVal.value / (this.maxX - this.minX);
    }

    this.ySVGToGraph = function(y) {
        return (this.svg.height.baseVal.value - y) * (this.maxY - this.minY) / this.svg.height.baseVal.value + this.minY;
    }

    this.yGraphToSVG = function(y) {
        return this.svg.height.baseVal.value - (y - this.minY) * this.svg.height.baseVal.value / (this.maxY - this.minY);
    }

    this.drawGrid = function() {
        for(var x = this.minX; x <= this.maxX; x += this.stepX) {
            var i = this.xGraphToSVG(Math.pow(10, x));
            var line = this.doc.createElementNS(this.ns, "line");
            line.setAttribute("x1", i);
            line.setAttribute("y1", 0);
            line.setAttribute("x2", i);
            line.setAttribute("y2", this.svg.height.baseVal.value);
            line.setAttribute("style", "fill:none;stroke:lightgrey;stroke-width:2");
            this.svg.appendChild(line);
            this.gridElements.push(line);
            var text = this.doc.createElementNS(ns, "text");
            text.setAttribute("x", i + 3);
            text.setAttribute("y", this.svg.height.baseVal.value - 3);
            text.setAttribute("fill", "black");
            text.setAttribute("font-family", "Verdana");
            text.setAttribute("font-size", "12");
            if(x >= 0) text.textContent = "1e+" + x;
            else text.textContent = "1e" + x;
            this.svg.appendChild(text);
            this.gridElements.push(text);
        }
        for(var y = this.minY + this.stepY; y <= this.maxY; y += this.stepY) {
            var i = this.yGraphToSVG(y);
            var line = this.doc.createElementNS(this.ns, "line");
            line.setAttribute("x1", 0);
            line.setAttribute("y1", i);
            line.setAttribute("x2", this.svg.width.baseVal.value);
            line.setAttribute("y2", i);
            line.setAttribute("style", "fill:none;stroke:lightgrey;stroke-width:2");
            this.svg.appendChild(line);
            this.gridElements.push(line);
            var text = this.doc.createElementNS(this.ns, "text");
            text.setAttribute("x", 3);
            text.setAttribute("y", i - 3);
            text.setAttribute("fill", "black");
            text.setAttribute("font-family", "Verdana");
            text.setAttribute("font-size", "12");
            text.textContent = parseFloat(y).toFixed(2);
            this.svg.appendChild(text);
            this.gridElements.push(text);
        }
    }

    this.addFunction = function(f, color) {
        var polyline = this.doc.createElementNS(this.ns, "polyline");
        polyline.setAttribute("style", "fill:none;stroke:" + color + ";stroke-width:2");
        for(var cx = 0; cx - 1 < this.svg.width.baseVal.value; cx += 1) {
            var gx = this.xSVGToGraph(cx);
            var gy = f(gx);
            var cy = this.yGraphToSVG(gy);
            var point = this.svg.createSVGPoint();
            point.x = cx;
            point.y = cy;
            polyline.points.appendItem(point);
        }
        polyline.f = f;
        this.functions.push(polyline);
        this.svg.appendChild(polyline);
        return polyline;
    }

    this.reDraw = function() {
    	this.gridElements.forEach(function(e){this.svg.removeChild(e)});
        this.gridElements = [];
        this.drawGrid();
        var self = this;
        this.functions.forEach(function(f){
            self.svg.removeChild(f);
            for(var i=0; i<f.points.length; i++) {
                var p = f.points[i];
                p.y = self.yGraphToSVG(f.f(self.xSVGToGraph(p.x)));
            }
            self.svg.appendChild(f);
        });
        this.points.forEach(function(p){
            self.svg.removeChild(p);
            p.setAttribute("cx", self.xGraphToSVG(p.gx));
            p.setAttribute("cy", self.yGraphToSVG(p.gy));
            self.svg.appendChild(p);
        });
    }

	this.addPoint = function(cx, cy) {
        var point = this.doc.createElementNS(this.ns, "circle");
        point.setAttribute("cx", cx);
        point.setAttribute("cy", cy);
        point.setAttribute("r", 5);
        point.gx = this.xSVGToGraph(cx);
        point.gy = this.ySVGToGraph(cy);
        this.svg.appendChild(point);
        this.points.push(point);
        return point;
    }

    this.tryRemovePoint = function(cx, cy) {
        var minIndex = -1;
        var minDist = 64;
        for (var i = this.points.length - 1; i >= 0; i--) {
            var otherPoint = this.points[i];
            var dist = Math.pow(otherPoint.getAttribute("cx") - cx, 2) + Math.pow(otherPoint.getAttribute("cy") - cy, 2);
            if(dist < minDist) {
                minIndex = i;
                minDist = dist;
            }
        }
        if(minDist < 64) {
            var point = this.points[minIndex];
            this.svg.removeChild(point);
            this.points.splice(minIndex, 1);
            return point;
        }
        return null;
    }

    this.drawGrid();
}