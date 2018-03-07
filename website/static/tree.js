function shadeColor2(color, percent) {
    var f=parseInt(color.slice(1),16),t=percent<0?0:255,p=percent<0?percent*-1:percent,R=f>>16,G=f>>8&0x00FF,B=f&0x0000FF;
    return "#"+(0x1000000+(Math.round((t-R)*p)+R)*0x10000+(Math.round((t-G)*p)+G)*0x100+(Math.round((t-B)*p)+B)).toString(16).slice(1);
}
function blendColors(c0, c1, p) {
    var f=parseInt(c0.slice(1),16),t=parseInt(c1.slice(1),16),R1=f>>16,G1=f>>8&0x00FF,B1=f&0x0000FF,R2=t>>16,G2=t>>8&0x00FF,B2=t&0x0000FF;
    return "#"+(0x1000000+(Math.round((R2-R1)*p)+R1)*0x10000+(Math.round((G2-G1)*p)+G1)*0x100+(Math.round((B2-B1)*p)+B1)).toString(16).slice(1);
}

function modify_node(node, depth=1) {
  node.text = ' <small>' + node.rank.name + ': </small>' + node.name;
  if(node.get_top_common_name) {
    node.text += ' <span class="common-names">(' + node.get_top_common_name + ')</span>';
  }
  if(node.get_latest_assessment) {
    node.text += ' <span class="assessment assessment-' + node.get_latest_assessment + '">' + node.get_latest_assessment + '</span>';
  }
  node.icon = 'glyphicon glyphicon-leaf';
  node["li_attr"] = { "class" : "tree-depth-" + node.rank.id,
    "style" : "color: " +  blendColors('#f0ac28', '#0c61a9', node.rank.id/9) }

  if(current_pk == node.id && node.rank.id != 9 && node.rank.id != 1 && node.rank.id != 2) {
    node['li_attr']['class'] += ' tree-highlight-node';
  }
  if(node['children'].length > 0) {
    node.state = {'opened': true};
    node['children'].forEach(modify_node, depth + 1);
  } else {
    node['children'] = node.child_count > 0
  }
};

function tree_view() {
  $('#jstree').on('select_node.jstree', function (e, data) {
      node = data.node;
      if((node.original.rank.id == 8 || node.original.rank.id == 10) && node.original.child_count == 0) {
        window.location.href = taxaDetailUrl.slice(0, -1) + node.id;
      } else {
        data.instance.toggle_node(data.node);
      }
      //data.instance.toggle_node(data.node);
  })
  .jstree({
    "core" : {
      "animation" : 0,
      "check_callback" : true,
      "themes" : { "stripes" : true },
      'data' : {
        'url' : function (node) {
          if(node.id == '#') {
            return getChildrenUrl.slice(0, -1) + current_pk + '?format=json';
          } else {
            return getChildrenUrl.slice(0, -1) + node.id + '?format=json';
          }
        },
        'dataFilter': function(data, type) {
          // I have no idea why, but you seem to have to double parse and double stringify everything...
          temp = JSON.stringify(data).replace(/parent/g, '_parent')
          temp = JSON.parse(JSON.parse(temp));
          modify_node(temp, '');
          temp = JSON.stringify(JSON.stringify(temp));
          temp = JSON.parse(temp);

          // output = JSON.stringify(data).replace(/name/g, 'text').replace(/parent/g, '_parent');
          // output = JSON.parse(output);
          return temp;
        },
        'data' : function (node) {
          return {
            'id' : node.id,
            'state': {'opened': true},
          };
          // return { 'id' : node.id };
        }
      }
    },
    "types" : {
      "#" : {
        "max_children" : 1,
        "max_depth" : 4,
        "valid_children" : ["root"]
      },
      "root" : {
        "icon" : "/static/3.3.3/assets/images/tree_icon.png",
        "valid_children" : ["default"]
      },
      "default" : {
        "icon" : "/static/3.3.3/assets/images/tree_icon.png",
        "valid_children" : ["default","file"]
      },
      "file" : {
        "icon" : "glyphicon glyphicon-th",
        "valid_children" : []
      }
    },
    "plugins" : ["contextmenu", "dnd", "types", "sort"]
  });
}