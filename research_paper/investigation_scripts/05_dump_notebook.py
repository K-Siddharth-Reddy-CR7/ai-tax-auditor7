import nbformat,sys
nb=nbformat.read(sys.argv[1],as_version=4)
print('cells',len(nb.cells), nb.metadata.get('kernelspec'), nb.metadata.get('language_info',{}).get('version'))
for i,c in enumerate(nb.cells):
    src=c.source
    outs=''
    if c.cell_type=='code':
        for o in c.get('outputs',[]):
            if o.output_type=='stream': outs+=o.text
            elif o.output_type in('execute_result','display_data'):
                d=o.get('data',{}); outs+= d.get('text/plain','') if 'image/png' not in d else '[IMAGE] '+d.get('text/plain','')
            elif o.output_type=='error': outs+='ERROR '+o.ename+': '+o.evalue
    print(f'\n######## CELL {i} [{c.cell_type}] exec={c.get("execution_count")}\n{src}\n--- OUT ---\n{outs[:1500]}')
