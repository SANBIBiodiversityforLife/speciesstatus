CKEDITOR.dialog.add( 'biblioDialog', function( editor ) {
    return {
        title: 'Insert a reference',
        minWidth: 400,
        minHeight: 100,

        contents: [
            {
                id: 'biblio',
                elements: [
                    {
                        id: 'data-doi',
                        type: 'text',
                        label: 'Select a reference by inserting a DOI',
                        setup: function( widget ) { this.setValue( widget.data['data-doi'] ); },
                        commit: function( widget ) { widget.setData( 'data-doi', this.getValue() ); },
                    },
                    {
                        type: 'button',
                        id: 'getBibtex',
                        label: 'Get citation',
                        title: 'Get citation',
                        onClick: function() {
                            // this = CKEDITOR.ui.dialog.button
                            dialog = this.getDialog()
                            doi = dialog.getValueOf('biblio', 'data-doi');
                            $.ajax({url: '/biblio/api/get-bibtex/' + doi,
                              dataType: 'json',
                              success: function(result){
                                dialog.setValueOf('biblio', 'data-bibtex', result);
                                bibtex_js_draw();
                                console.log('hi');
                                console.log($(".bibtex_input").val());
                              },
                              error: function(jqXHR, textStatus, errorThrown) {
                              }
                            });
                        }
                    },
                    {
                        type: 'html', 
                        html: '<h3>Citation preview</h3><div class="citation-preview" id="bibtex_display"></div>',
                        
                    },
                    {
                        id: 'data-bibtex',
                        className: 'bibtex_input',
                        type: 'textarea',
                        rows: 10,
                        label: 'Bibtex',
                        setup: function( widget ) { this.setValue( widget.data['data-bibtex'] ); },
                        commit: function( widget ) { widget.setData( 'data-bibtex', this.getValue() ); },
                    },
                ]
            },
        ]
    };
});