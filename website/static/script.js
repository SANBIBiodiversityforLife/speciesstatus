$(document).ready(function() {
	$("#explore").on('click', function(e) {

	// prevent default anchor click behavior
	e.preventDefault();

	// store hash
	var hash = this.hash;

	// animate
	
	$('html, body').animate(
		{ scrollTop: $(hash).offset().top }, 
		1000, 
		function(){
			window.location.hash = hash;
		});
	});
	
	
	
	width = $('#svgcontainer').width();
	console.log(width);
	console.log($('#svgcontainer').height());
	height = lineage[lineage.length - 1]['rank']* 150;
	//$('#lifetree').height(height + 'px');
	$('#lifetree').attr('height', height + 'px');
	
	//document.getElementById('lifetree').setAttribute("height", height + 'px');
	
	console.log(height);
	console.log($('#svgcontainer').height());
	
	
	
	// Now we shall construct our tree from the drilldown info
	
	// create a name: node map
	var dataMap = lineage.reduce(function(map, node) {
		map[node.name] = node;
		return map;
	}, {});
	
	// create the tree array
	var treeData = [];
	lineage.forEach(function(node) {
		// add to parent
		var parent = dataMap[node.parent];
		if (parent) {
			// For each of the children, replace the simple child 
			parent.children.forEach(function(child, i) {
				if(child['pk'] == node['pk']) {
					parent.children[i] = node;
				}
			});
		} else {
			// parent is null or missing
			treeData.push(node);
		}
	});
	
	// Hierarchical data is now contained in treeData
	var data = treeData[0];
	
	// Instantiate the variables
	var svg = d3.select("svg"), // Select the svg element in the DOM
		g = svg.append("g").attr("transform", "translate(40,40)"); // Inserts a group container and moves it 40 px right
	
	
	
	// D3 requires a hierarchy object which then gets made into a tree
	var root = d3.hierarchy(data);
	
	// Create a d3 tree object of the correct width and height
	var tree = d3.tree().size([width-200, height - 160]);
	
	tree(root);
	
	// Add the node elements to the svg group using data from root.descendants()
	var node = g.selectAll(".node")
		.data(root.descendants())
		.enter().append("g")
		.attr("class", function(d) { return "rank-" + d.data.rank + " node" + (d.children ? " node--internal" : " node--leaf"); })
		.attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });
	
	// Color manip stuff goes here
	function shadeColor2(color, percent) {   
		var f=parseInt(color.slice(1),16),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=f>>16,G=f>>8&0x00FF,B=f&0x0000FF;
		return "#"+(0x1000000+(Math.round((t-R)*p)+R)*0x10000+(Math.round((t-G)*p)+G)*0x100+(Math.round((t-B)*p)+B)).toString(16).slice(1);
	}
	
	function blendColors(c0, c1, p) {
		var f=parseInt(c0.slice(1),16),t=parseInt(c1.slice(1),16),R1=f>>16,G1=f>>8&0x00FF,B1=f&0x0000FF,R2=t>>16,G2=t>>8&0x00FF,B2=t&0x0000FF;
		return "#"+(0x1000000+(Math.round((R2-R1)*p)+R1)*0x10000+(Math.round((G2-G1)*p)+G1)*0x100+(Math.round((B2-B1)*p)+B1)).toString(16).slice(1);
	}
	var main_color = '#E84D00';
	var main_color = '#EFF3F7';
	var main_color = '#FFFFFF';
	var secondary_color = '#56E000';
	var secondary_color = '#FFFD93';
	var secondary_color = '#193758';
	var secondary_color = '#FFFFFF';
	var line_color = '#FFF793';
	var max_rank = lineage[lineage.length - 1]['rank'];
	
	function get_rank_colour(d) {
		rank = d.data.rank;
		if(rank == 9) {
			return main_color;
		}
		else {
			return blendColors(main_color, secondary_color, (d.data.rank / max_rank))
		}
	}
	
	// Add circles above
	node.append("circle")
		.attr("r", 2)
		.attr("transform", function(d) { return "translate(0,-18)"; })
		.attr("class", "upper-circle")
		.style("stroke", get_rank_colour)
		.style("fill", get_rank_colour);
	node.append("circle")
		.attr("r", 4)
		.attr("transform", function(d) { return "translate(0,16)"; })
		.attr("class", "lower-circle")
		.style("stroke", get_rank_colour)
		.style("fill", "#000000");

	// Add text
	node.append("text")
		.attr("dy", 3)
		.style("fill", get_rank_colour)
		//.attr("x", function(d) { return d.children ? -8 : 8; })
		.attr("x", function(d) { return d.name })
		.style("text-anchor", "middle")
		//.style("text-anchor", function(d) { return d.children ? "end" : "start"; })
		.text(function(d) { 
			if(d.children && d.data.rank != 9 && d.data.rank != 1) {
				return d.data.name + " (" + d.children.length + ")";
			}
			return d.data.name;
		})
		.each(function(d) { 
			d.textwidth = this.getBBox().width;;
			d.textheight = this.getBBox().height;;
		});
	
	node.insert("rect",":first-child")
		.style("fill", '#000000')
		.style("fill-opacity", 0.2)
		.attr('height', function(d) { return d.textheight + 10; })
		.attr('width', function(d) { return d.textwidth + 10; })
		.attr("transform", function(d) { 
			if(d.data.rank == 9) {
				return "translate(-" +  ((d.textwidth + 10) / 2) + ",-" +  ((d.textheight + 30) / 2) + ")"; 
			}
			return "translate(-" +  ((d.textwidth + 10) / 2) + ",-" +  ((d.textheight + 15) / 2) + ")"; 
		})
		.attr('rx', 10)
		.attr('ry', 10);
	
	
	
	// Declare the links…
	var link = g.selectAll(".link")
	    .data(root.descendants().slice(1).reverse())
		.enter().insert("path",":first-child")
		.attr("class", "link")	
		//.style("stroke", function(d) { return shadeColor2(main_color, (d.data.rank / max_rank) ) })
		.style("stroke", function(d) { 
			if(d.children) {
				return line_color;
			}
			return blendColors(main_color, secondary_color, (d.data.rank / max_rank)) 
		})
		.attr("d", function(d) {
			return 'M' + d.x + ',' + (d.y - 18)
			+ "C" + (d.x + d.parent.x) / 2 + "," + (d.y - 25)
			+ " " + (d.x + d.parent.x) / 2 + "," + (d.parent.y + 25)
			+ " " + d.parent.x + "," + (d.parent.y + 17);
		});
		
	// Trianglify background]
	var params = { height: $('#triangles').height(), 
		width: $('#triangles').width(),
  x_colors: 'Blues',
  y_colors: 'match_x' };	
	var temp = document.getElementById('triangles');
	var pattern = new Trianglify(params);
	$('#triangles').attr('style', 'background: url(' + pattern.png() + ') no-repeat center center');
	
	
	$('g').hover(function() {
		//$(this).children('rect').style('fill', 'red');
		//$(this).children('rect').attr('fill-opacity', 1);
		//$(this).children('rect').attr('opacity', 1);
		$(this).children('rect').addClass('recthover');
	}, function() {
		$(this).children('rect').removeClass('recthover');
	});
	
});