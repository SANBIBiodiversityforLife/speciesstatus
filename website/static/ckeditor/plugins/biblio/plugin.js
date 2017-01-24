CKEDITOR.plugins.add('biblio', {
    requires: 'widget',
    icons: 'biblio',
    init: function(editor) {
        
		
		// editor.addCommand('biblio', new CKEDITOR.dialogCommand('biblioDialog'));

		/*
		editor.ui.addButton( 'Biblio', {
			label: 'Insert Reference',
			command: 'biblio',
			toolbar: 'insert'
		});*/
		
		CKEDITOR.dialog.add( 'biblioDialog', this.path + 'dialogs/biblio.js' );

        editor.widgets.add( 'biblio', {
            button: 'Insert reference',
            template: '<span class="biblio" id="">Reference</span>',
            editables: {},
            allowedContent: 'span[*]',
            dialog: 'biblioDialog',
            upcast: function( element ) {
                return element.name == 'span' && element.hasClass( 'biblio' );
            },
            init: function() {
                bibtex = $(this.element).attr('data-bibtex');
                if(bibtex)
                    this.setData('data-bibtex', bibtex);
            },
            data: function() {
              if (this.data['data-bibtex']) {
                this.setData('data-bibtex', this.data['data-bibtex']);
                this.element.setAttribute('data-bibtex', this.data['data-bibtex']);
        
                // Set a throbber so the user knows we are bibtexng something
                this.element.getChild(0).setAttribute('src', '/static/img/throbber.gif');
                
                // Try and get the bibtex from the database
                $.ajax({url: '/biblio/get-bibtex/' + this.data['data-bibtex'],
                  dataType: 'json',
                  success: function(result){
                    console.log('success');
                    console.log(result);

                    ele.setAttribute('data-aw-copyright', result.copyright);
                    ele.getChild(0).setAttribute('src', result.thumbnail_preview_url);
                  },
                  error: function(jqXHR, textStatus, errorThrown) {
                    console.log('error');
                    console.log(errorThrown);
                  }
                });
              };
            }
        });
    }
});