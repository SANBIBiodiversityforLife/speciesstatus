$(document).ready(function() {
  // Lineage variable should contain a flat set of elements with parent/child attributes, we need to turn it into a tree
  // Create the tree array http://stackoverflow.com/a/38900233/4034849 
  function unflatten(treeArray, parent) {
    var dTree = {};
    
    // Get the parent, this is the one we're working on. When we first initiate it, set it to 0
    parent = typeof parent !== 'undefined' ? parent : {id: 0};
    
    // Find all of the nodes which are children to this parent
    var childrenArray = treeArray.filter(function(child) {
      return child.parent == parent.id;
    });

    if (childrenArray.length > 0) {
      if (parent.id == 0) { // Frankly i don't understand why this works
        dTree = childrenArray;
      } else {
        // Keep on setting children
        parent['children'] = childrenArray;
      }
      
      // Loop over all the children and do the same to them
      // I guess objects are immutable in js, so once you go into the function and 
      // start setting the children for every object it gets set everywhere
      childrenArray.forEach(function(child) {
        unflatten(treeArray, child);
      })
    }

    return dTree;
  }; 
  
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
			return blendColors(main_color, secondary_color, (d.data.data.rank / max_rank))
		}
	}

	// Transition vars
	var duration = 750;

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
    //console.log(json);
    
    // Set life parent to 0, that's what our function above needs
    //json[0].parent = 0;
    
    // Save the flat lineage, we have to do this weird parse thing to make a deep copy
    lineage_flat = JSON.parse(JSON.stringify(json));
    
    //dataTree = unflatten(json);
    var temp1 = JSON.parse(JSON.stringify(json));
    temp1[0].parent = 0;
    var dt = unflatten(temp1); 
    console.log(dt);
    
    var dataTree = d3.stratify()
      .id(function(d){ return d.id; })
      .parentId(function(d){  return d.parent; })
      (json);
    console.log(dataTree);
    //var dataTree = stratify(json);
    //temp = JSON.parse(JSON.stringify(dataTree));
    
    //console.log('tree');
    //console.log(temp[0]['children'][0]['children'][0]['children'][0]['children'][0]);

    // D3 requires a hierarchy object which then gets made into a tree
    var root = d3.hierarchy(dataTree);
    //var root = d3.hierarchy(dataTree[0]);

    tree(root);
    //console.log(root['children'][0]['children'][0]['children'][0]['children'][0]);
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
      .attr("r", 4)
      .attr("transform", function(d) { return "translate(0,16)"; })
      .attr("class", "lower-circle")
      .style("stroke", get_rank_colour)
      .style("fill", "#000000");

    // Add text
    node.append("text")
      .attr("dy", 3)
      .style("fill", get_rank_colour)
      .attr("x", function(d) { return d.name })
      .style("text-anchor", "middle")
      .text(function(d) {console.log(d);
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
    node.insert("rect",":first-child")
      .style("fill", '#000000')
      .style("fill-opacity", function(d) {
          if(d.children || d.data.rank == max_rank) { return 0.5; }
          else { return 0.2; }
        }
      )
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
  }

  function updateTree(source, shallowestDepth = 0) {
    // Data join with source data, keeping ids so it knows about the same nodes
    var node = g.selectAll(".node")
      .data(source.descendants() , function(d) { return d.data.id; });
    var link = g.selectAll(".link")
      .data(source.descendants().slice(2).reverse())
      //.data(source.descendants().slice(1).reverse())
    
    // Remove old elements first, with a transition
    // Find the shallowest depth in the old element, that's the parent
    var oldNode = node.exit();
    var oldLink = link.exit();
    
    oldNode.transition()
      .duration(duration)
      .attr("transform", function(d) { 
        // Get the parent they have to contract into
        var shallowestParent = d;
        do { shallowestParent = shallowestParent.parent; }
        while(shallowestParent.depth > shallowestDepth);
        return "translate(" + shallowestParent.x + "," + shallowestParent.y + ")"; 
      })
      .remove();
    oldLink.transition()
      .duration(duration)
      .attr("d", function(d) {
        // Get the parent they have to contract into
        var shallowestParent = d;
        do { shallowestParent = shallowestParent.parent; }
        while(shallowestParent.depth > shallowestDepth);
        console.log(shallowestParent);
        return 'M' + d.x + ',' + (d.y - 18)
        + "C" + (d.x + shallowestParent.x) / 2 + "," + (d.y - 25)
        + " " + (d.x + shallowestParent.x) / 2 + "," + (shallowestParent.y + 25)
        + " " + shallowestParent.x + "," + (shallowestParent.y + 17);
      })
      .remove();
    
    
    // Data enter, this starts doing things to all the new nodes
    var newNodes = node.enter()
      .append("g")
      .attr("class", function(d) { return "rank-" + d.data.rank + " node" + (d.children ? " node--internal" : " node--leaf"); })
      .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; })
      .on("click", click);
    
    
    // Add text + bg + circles to the nodes
    drawElements(newNodes);
    
    
    // Add pretty hover class for each taxon node
    $('g').hover(function() {
      $(this).children('rect').addClass('recthover');
    }, function() {
      $(this).children('rect').removeClass('recthover');
    });

    // Transition nodes to their new position.
    //node.transition()
    //    .duration(duration)
    //    .attr("transform", function(d) { return "translate(" + d.x + "," + d.y + ")"; });


    // Draw the links between nodes
    var link = g.selectAll(".link")
      .data(source.descendants().slice(1).reverse())
      .enter().insert("path",":first-child")
      .attr("class", "link")
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
      /*.attr("d", function(d) {
        return 'M' + d.x0 + ',' + (d.y0 - 18)
        + "C" + (d.x0 + d.parent.x0) / 2 + "," + (d.y0 - 25)
        + " " + (d.x0 + d.parent.x0) / 2 + "," + (d.parent.y0 + 25)
        + " " + d.parent.x0 + "," + (d.parent.y0 + 17);
      });*/

    // Transition links to their new position.
    // link.transition().duration(duration)

    // Transition exiting nodes to the parent's new position.
    /*link.exit().transition()
        .duration(duration)
        .attr("d", function(d) {
          return 'M' + source.x + ',' + (source.y - 18)
          + "C" + (source.x + source.parent.x) / 2 + "," + (source.y - 25)
          + " " + (source.x + source.parent.x) / 2 + "," + (source.parent.y + 25)
          + " " + source.parent.x + "," + (source.parent.y + 17);
        })
        .remove();

    // Stash the old positions for transition.
    node.each(function(d) {
      d.x0 = d.x;
      d.y0 = d.y;
    });*/
  }
  

  // Toggle children on click.
  function click(d) {
    // If the node does not have any pre-loaded children
    if (!d.children && !d._children) {
      var jsonPath = '/taxa/api/children/' + d.data.id;
      
      // Get the JSON lineage for it
      d3.json(jsonPath, function(error, json) {
        // Add parent to lineage as a proper object
        // lineage.push(json['parent']);
        
        // Get the children
        children = json['children'];
        
        // Iterate through the lineage and hide the children for the siblings of the same rank as the pushed node
          /*lineage.forEach(function(node, i) {
            console.log('index ' + i + ' /// node rank' + node.rank + ' / ' + node.name)
          });
          forDel = []*/
          //console.log(children);  
          new_lineage = [];
        lineage_flat.forEach(function(node, i) {
            recalcIndex = lineage.indexOf(node);
          //console.log('index ' + recalcIndex + ' node rank ' + node.rank + ' / ' + node.name + ' vs clicked thing rank ' + d.data.rank )
          if(node.rank > d.data.rank && node.rank != 9) {
            //console.log('removing ' + recalcIndex + ' ' + node.name);
            //lineage.splice(recalcIndex, 1);
            
          }
          else {
            //node._children = node.children;
            //delete node.children;
            new_lineage.push(node);
            
          }
          //else if(node.rank == d.data.rank && node.id != d.data.id) {
            
            //node._children = node.children;
            //node.children = [];
          //}
        });
        
        //lineage = new_lineage;
        //console.log('ffff'); console.log(lineage);
        children.forEach(function(child) {
          new_lineage.push(child);
        });
        temp = JSON.parse(JSON.stringify(new_lineage));
        new_lineage = JSON.parse(JSON.stringify(temp));

        root = getTreeData(new_lineage);
        
        //console.log(root['children'][0]['children'][0]['children'][0]['children'][0]);
        //console.log(root);
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