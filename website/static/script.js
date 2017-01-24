$(document).ready(function() {  
	// WTF js.
	var lineage_flat;
  
	// Color manipulation functions and settings for the tree
	function shadeColor2(color, percent) {
		var f=parseInt(color.slice(1),16),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=f>>16,G=f>>8&0x00FF,B=f&0x0000FF;
		return "#"+(0x1000000+(Math.round((t-R)*p)+R)*0x10000+(Math.round((t-G)*p)+G)*0x100+(Math.round((t-B)*p)+B)).toString(16).slice(1);
	}
	function blendColors(c0, c1, p) {
		var f=parseInt(c0.slice(1),16),t=parseInt(c1.slice(1),16),R1=f>>16,G1=f>>8&0x00FF,B1=f&0x0000FF,R2=t>>16,G2=t>>8&0x00FF,B2=t&0x0000FF;
		return "#"+(0x1000000+(Math.round((R2-R1)*p)+R1)*0x10000+(Math.round((G2-G1)*p)+G1)*0x100+(Math.round((B2-B1)*p)+B1)).toString(16).slice(1);
	}
  
    // Color variables
	var main_color = '#FFFFFF';
	var secondary_color = '#FFFFFF';
	var line_color = '#FFF793';
	var max_rank = lineage[lineage.length - 1]['rank'];

	// Used to assign colors to ranks
	function get_rank_colour(d) {
		rank = d.data.data.rank;
		if(rank == 9) {
			return main_color;
		}
		else {
			return blendColors(main_color, secondary_color, (d.data.rank / max_rank))
		}
	}
  
	// Draws a curve between two points
	function connector(d) {
	return 'M' + d.x + ',' + (d.y - 18) +
	  "C" + (d.x + d.parent.x) / 2 + "," + (d.y - 25) +
	  " " + (d.x + d.parent.x) / 2 + "," + (d.parent.y + 25) +
	  " " + d.parent.x + "," + (d.parent.y + 17);
	};   

	// Transition vars
	var duration = 500;

  // Get the width of the container element for the tree
	width = $('#svgcontainer').width();

	// Calculate the height required based on the number of node levels on the ancestry tree
	height = lineage[lineage.length - 1]['rank']* 150;

	// Set the svg element's height
	$('#lifetree').attr('height', height + 'px');

  // Select the svg element in the DOM
  var svg = d3.select("svg")

  // Insert a group container and move it 40 px to the right (to pad the tree contents in the svg container)
  var g = svg.append("g").attr("transform", "translate(40,40)");

  // Create and return a d3 tree object of the correct width and height, run the root hierarchy element through it
  var tree = d3.tree().size([width-200, height - 160]);
  var root = getTreeData(lineage);
  updateTree(root);

  // Get the data for the tree
  function getTreeData(json) {    
    // Save the flat lineage, we have to do this weird parse thing to make a deep copy
    lineage_flat = JSON.parse(JSON.stringify(json));
    
    // This seems to unflatten arrays of objects with parentIds and parents. Wish I'd known about it sooner.
    var dataTree = d3.stratify()
      .id(function(d){ return d.id; })
      .parentId(function(d){  return d.parent; })
      (JSON.parse(JSON.stringify(json)));

    // D3 requires a hierarchy object which then gets made into a tree
    var root = d3.hierarchy(dataTree);
    tree(root);
    
    // Normalize for fixed-depth, also we do some fancy transitions so save a copy of original xys
    root.each(function(d) { d.y = d.depth * 100; d.x0 = d.x; d.y0 = d.y; });
    return root;
  }

  function drawElements(node) {
    // Add circles above each node
    node.append("circle")
      .attr("r", 2)
      .attr("transform", function(d) { return "translate(0,-18)"; })
      .attr("class", "upper-circle")
      .style("stroke", get_rank_colour)
      .style("fill", get_rank_colour);

    // Add the circles below each node
    node.append("circle")
      .attr("r", 5)
      .attr("transform", function(d) { return "translate(0,16)"; })
      .attr("class", "lower-circle")
      .style("stroke", "#000000")
      .style("fill", function(d) {
        return d.data.data.child_count > 0 ? "#FFFFFF" : "#000000";
      })
      .on("click", click);

    // Add text
    var textGroup = node.append('g').attr('class', 'text-group').append("svg:a")
      .attr("xlink:href", function(d){ return taxaDetailUrl.slice(0, -1) + d.data.id; })  ;
    textGroup.append("text")
      .attr("dy", 3)
      .style("fill", '#FFFFFF')
      .style("text-anchor", "middle")
      .text(function(d) {
        return d.data.data.name;
        if(d.data.rank == max_rank || d.data.name == "Life") {
          return d.data.name;
        }
        else if(d.children) {
          return d.data.name + ' (' + d.children.length + ")";
        }
        else {
          return d.data.name + ' (' + d.data.count + ")";
        }
      })
      .each(function(d) {
        d.textwidth = this.getBBox().width;
        d.textheight = this.getBBox().height;
      });

    // Add clickable background rectangle so it looks nicer
    textGroup
      .insert("rect",":first-child")
      .style("fill-opacity", function(d) {
          if(d.children || d.data.data.rank == max_rank) { return 0.5; }
          else { return 0.2; }
        }
      )
      .attr('height', function(d) { return d.textheight + 10; })
      .attr('width', function(d) { return d.textwidth + 10; })
      .attr("transform", function(d) {
        if(d.data.data.rank == 9) {
          return "translate(-" +  ((d.textwidth + 10) / 2) + ",-" +  ((d.textheight + 30) / 2) + ")";
        }
        return "translate(-" +  ((d.textwidth + 10) / 2) + ",-" +  ((d.textheight + 15) / 2) + ")";
      })
      .attr('rx', 10)
      .attr('ry', 10);
  }

  function updateTree(source, shallowestDepth = 0) {
    /* 
     * Nodes
     */
    // Data join with source data, keeping ids so it knows about the same nodes
    var node = g.selectAll(".node")
      .data(source.descendants() , function(d) { return d.data.id; });
    
    // Data enter, this starts doing things to all the new nodes
    var nodeEnter = node.enter()
      .append("g")
      .attr("class", function(d) { return "rank-" + d.data.data.rank + " node" + (d.children ? " node--internal" : " node--leaf"); })
      .attr("transform", function(d) {
        if(d.parent != null) {
          return "translate(" + d.parent.x + "," + d.parent.y + ")";
        }
        return "translate(" + d.x + "," + d.y + ")"; 
      });
    
    // Add text + bg + circles to the nodes
    drawElements(nodeEnter);
    
    // Transition nodes to their new position.
    var nodeMerge = node.merge(nodeEnter).transition()
      .duration(duration)
      .attr('transform', function (d) {
        return 'translate(' + d.x + ',' + d.y + ')';
      });
    nodeMerge.select('rect', ':first-child').style("fill-opacity", function(d) {
      if(d.children || d.data.data.rank == max_rank) { return 0.5; }
      else { return 0.2; }
    });
      
    // Get the old elements for removal
    var oldNode = node.exit();
    
    // Find the shallowest depth in the old element, that's the parent
    oldNode.each(function(d) {
        var shallowestParent = d;
        do { shallowestParent = shallowestParent.parent; }
        while(shallowestParent.depth > shallowestDepth);
        d.shallowestParentX = shallowestParent.x;
        d.shallowestParentY = shallowestParent.y; 
    });
    
    // Transition the old nodes out
    var transitionedNodes = oldNode.transition()
      .duration(duration)
      .attr("transform", function(d) { 
        return "translate(" + d.shallowestParentX + "," + d.shallowestParentY + ")"; 
      });
    oldNode.selectAll('rect').transition()
      .style("fill-opacity", 0)
      .duration(duration/2)
    oldNode.selectAll('text').transition()
      .style("fill-opacity", 0)
      .duration(duration/2)
    oldNode.selectAll('circle').transition()
      .style("fill-opacity", 0)
      .duration(duration/3)
    transitionedNodes.remove();
    
    /* 
     * Links
     */
    var link = g.selectAll(".link")
      .data(source.descendants().slice(1).reverse(), function(d) { return d.data.id; })
    
    // Draw the links between nodes
    var linkEnter = link.enter()
      .insert("path",":first-child")
      .attr("class", "link")
      .style("stroke", function(d) {
        if(d.children) {
          return line_color;
        }
        return blendColors(main_color, secondary_color, (d.data.data.rank / max_rank))
      })
      .attr("d",  function (d) {
        var o = {x: d.parent.x0, y: d.parent.y0, parent: {x: d.parent.x0, y: d.parent.y0}};
        return connector(o);
      });
      
    // Transition links to their new position.
    var linkMerge = link.merge(linkEnter).transition()
      .duration(0)
      .attr('d', connector);
      
    // Style the links
    linkMerge.style("stroke", function(d) {
      if(d.children) {
        return line_color;
      }
      return blendColors(main_color, secondary_color, (d.data.data.rank / max_rank))
    })
    
    // Transition the old links out
    var oldLink = link.exit();
    oldLink.transition()
      .duration(duration/2)
      .attr("d", function(d) {
        var o = {x: d.x, y: d.y, parent: {x: d.x, y: d.y}};
        return connector(o);
      })
      .remove();
  }
  
  // Toggle children on click.
  function click(d) {
    // If the node does not have any pre-loaded children
    if (!d.children && !d._children) {
      var jsonPath =  getChildrenUrl.slice(0, -1) +  d.data.id;
      
      // Get the JSON lineage for it
      d3.json(jsonPath, function(error, json) {
        // Get the children
        children = json['children'];
        
        // Make a new lineage array, can't use the one previously stored because
        // of javascript variables mutability being weird
        new_lineage = [];
        lineage_flat.forEach(function(node, i) {
          recalcIndex = lineage.indexOf(node);
          // The node.rank 9 is in there because Life for some reason has rank 9
          // Basically we want to exclude all nodes of a lower rank than the one clicked
          if(node.rank > d.data.data.rank && node.rank != 9) {           
            // console.log(node); - we don't want these nodes
          }
          else { new_lineage.push(node); }
        });
        
        // Append the children to the new lineage
        children.forEach(function(child) {
          new_lineage.push(child);
        });
        
        // Javascript is weird. We need a deep copy of new_lineage
        temp = JSON.parse(JSON.stringify(new_lineage));
        new_lineage = JSON.parse(JSON.stringify(temp));
        
        // Turn it into a tree and update our svg
        root = getTreeData(new_lineage);
        updateTree(root, d.depth);
       });
    }
  }

	// Trianglify background
	var params = {  height: $('#triangles').height(),
                  width: $('#triangles').width(),
                  x_colors: 'Blues',
                  y_colors: 'match_x' };
	var temp = document.getElementById('triangles');
	var pattern = new Trianglify(params);
	$('#triangles').attr('style', 'background: url(' + pattern.png() + ') no-repeat center center');
});