
set encoding=utf-8
set nocompatible 

" Editing ---------------------------------------------------------------------------------------{{{

" MOUSE
"set mouse=a

" TABS
set expandtab                   "et:    uses spaces instead of tab characters
set smarttab                    "sta:   helps with backspacing because of expandtab
set tabstop=2                   "ts:    number of spaces that a tab counts for
set shiftwidth=2                "sw:    number of spaces to use for autoindent
set shiftround                  "sr:    rounds indent to a multiple of shiftwidth

" PHP
au FileType php set cindent     "cin:   enables the second-most configurable indentation (see :help C-indenting).
au FileType php set cinoptions=l1,c4,(s,U1,w1,m1,j1
au FileType php set cinwords=if,elif,else,for,while,try,except,finally,def,class
set showmatch                   "sm:    flashes matching brackets or parentheses

" FOLDING
set foldenable                  "fe:    enable folding
set foldmethod=marker           "fm:    use {{{}}} markers for forlding
set foldcolumn=1                "fdc:   creates a small left-hand gutter for displaying fold info
let php_folding=1               "auto fold php classes and functions
" toggle fold under cursor
noremap  <silent> <space> :exe 'silent! normal! za'.(foldlevel('.')?'':'l')<cr>
" open all folds
noremap  <silent> ,f zR
" close all folds
noremap  <silent> ,F zM

" MISC
set backspace=indent,eol,start  "bs:    allows you to backspace over the listed character types
set linebreak                   "lbr:   causes vim to not wrap text in the middle of a word
set wrap                        "wrap:  wraps lines by default
set nojoinspaces                "nojs:  prevents inserting two spaces after punctuation on a join (it's not 1990 anymore)
set listchars=tab:>-,eol:$      "lcs:   makes finding tabs easier during :set list
set lazyredraw                  "lz:    will not redraw the screen while running macros (goes faster)
set wildmenu                    "wm:    better tab completion in ex mode
set infercase                   "ic:    ignore case on insert completion
set textwidth=0                 "tw:    don't wrap lines at 78 chars
set noswapfile                  "unk:   don't create .swp files, they're at best (and at worst) annoying
" toggle paste mode
noremap ,v :set nopaste!<CR>:set nopaste?<CR>

" -----------------------------------------------------------------------------------------------}}}

" Search ---------------------------------------------------------------------------------------{{{

set incsearch                   "is:    automatically begins searching as you type
set ignorecase                  "ic:    ignores case when pattern matching
set smartcase                   "scs:   ignores ignorecase when pattern contains uppercase characters
set hlsearch                    "hls:   highlights search results

" Use ctrl-n to unhighlight search results in normal mode:
nmap <silent> ,h :silent noh<CR>  

" -----------------------------------------------------------------------------------------------}}}

" Some custom functions ---------------------------------------------------------------------------------------{{{


function! NextWordOrColumn ()
  let l:line = getline('.')
  if l:line =~ '^|.\+|\s*$'
    let l:hit_bar = 0
    for i in range(col('.'), len(l:line))
      if l:hit_bar
        if l:line[i] != ' ' && l:line[i] != '|'
          call cursor(line('.'), i+1)
          return
        endif 
      elseif l:line[i] == '|'
        let l:hit_bar = 1
      endif
    endfor
  else
    call feedkeys('w', 'n')
  endif
endfunction


function! PrevWordOrColumn ()
  let l:line = getline('.')
  if l:line =~ '^|.\+|\s*$'
    let l:hit_bar = 0
    let l:hit_val = 0
    for i in range(0, col('.'))
      let j = col('.') - i
      if l:hit_bar
         if l:hit_val && l:line[j] == ' '
                   call cursor(line('.'), j+2)
       return
         elseif l:line[j] != ' '
             let l:hit_val = 1
         endif 
      elseif l:line[j] == '|'
         let l:hit_bar = 1
      endif
    endfor
  else
    call feedkeys('b', 'n')
  endif
endfunction

" -----------------------------------------------------------------------------------------------}}}

" Navigation ---------------------------------------------------------------------------------------{{{

" modify paging commands
nmap <silent> <C-d> 25j
nmap <silent> <C-u> 25k

" modify word jumping, so we jump columns in MySQL
nnoremap <silent> w :<C-u>call NextWordOrColumn()<CR>
nnoremap <silent> b :<C-u>call PrevWordOrColumn()<CR>

" I want to go to the first non-\s char way more than I want col 0, and ^ sucks to type
noremap  <silent> 0 ^
noremap  <silent> ^ 0

" go to last changed text
noremap  <silent> t `.

" -----------------------------------------------------------------------------------------------}}}

" Windows and Tabs ---------------------------------------------------------------------------------------{{{

" switch tabs
nnoremap <Tab> gt

" quick window resize
nmap <C-l> :vertical res +1<CR>
nmap <C-k> :res +1<CR>
nmap <C-h> :vertical res -1<CR>
nmap <C-j> :res -1<CR>
nmap ,m :res +500<CR>
nmap ,a :NERDTreeToggle<CR>

" jumping between buffers
nnoremap <C-n> <C-w>j
nnoremap <C-p> <C-w>k

" NERDTree
let NERDChristmasTree=1

" rotate through buffers in tabline
noremap <silent> <F9> :<C-u>bprev<CR> 
noremap <silent> <F10> :<C-u>bnext<CR>

" toggle wrapping
nmap <silent> ,p :set nowrap!<CR>:set nowrap?<CR>

" Remember last position in file
au BufReadPost * if line("'\"") > 0 && line("'\"") <= line("$") | exe "normal g'\"" | endif

" MISC
"set winminheight=0              " I'm not sure why Vim displays one line by default when 'maximizing' a split window with ctrl-_
"set winminwidth=0               " I'm not sure why Vim displays one line by default when 'maximizing' a split window with ctrl-_
set number                      "nu:    numbers lines
set showmode                    "smd:   shows current vi mode in lower left
"set cursorline                 "cul:   highlights the current line
set showcmd                     "sc:    shows typed commands
set cmdheight=2                 "ch:    make a little more room for error messages
set scrolloff=2                 "so:    places a couple lines between the current line and the screen edge
set sidescrolloff=2             "siso:  places a couple lines between the current column and the screen edge
set laststatus=2                "ls:    makes the status bar always visible
set ttyfast                     "tf:    improves redrawing for newer computers
set viminfo='500,f1,:100,/100   "vi:    For a nice, huuuuuge viminfo file
set switchbuf=usetab            "swb:   Jumps to first window or tab that contains specified buffer instead of duplicating an open window
set showtabline=1               "stal:  Display the tabbar if there are multiple tabs. Use :tab ball or invoke Vim with -p
set hidden                      "hid:   allows opening a new buffer in place of an existing one without first saving the existing one
set equalalways                 "       allows winfixheight to work correctly

" -----------------------------------------------------------------------------------------------}}}

" Shell ---------------------------------------------------------------------------------------{{{

" Conque stuff
nmap ,t :<C-u>ConqueTerm bash<CR>
nmap ,T :<C-u>ConqueTermSplit bash<CR>
nmap ,s :<C-u>split scratch \| set nonumber foldcolumn=0 winfixheight<CR>
let g:ConqueTerm_PromptRegex = '^\[\w\+@[0-9A-Za-z_.-]\+:[0-9A-Za-z_./\~,:-]\+\]\$'
"let g:Conque_TERM = 'vt100'
"let g:Conque_Tab_Timeout = 10
"let g:ConqueTerm_ReadUnfocused = 0

redir >> /home/nraffo/.vim/echolog.log

" -----------------------------------------------------------------------------------------------}}}

" Colors and syntax ---------------------------------------------------------------------------------------{{{

" use 256 colors
set t_Co=256

syntax on                       "syn:   syntax highlighting
syn sync maxlines=500

" load all my syntax options
"source ~/.vim/syntax/mine.vim
set background=dark
colorscheme rdark-terminal

" -----------------------------------------------------------------------------------------------}}}

" Status line and Tab line ---------------------------------------------------------------------------------------{{{

function! MyStatusLine()
    let s = '%*' " restore normal highlighting
    let s .= '%%%n '
    if bufname('') != '' " why is this such a pain in the ass? FIXME: there's a bug in here somewhere. Test with a split with buftype=nofile
        let s .= "%{ pathshorten(fnamemodify(expand('%F'), ':~:.')) }" " short-hand path of of the current buffer (use :ls to see more info)
    else
        let s .= '%f' " an empty filename doesn't make it through the above filters
    endif
    let s .= '%m' " modified
    let s .= '%r' " read-only
    let s .= '%w' " preview window
    let s .= ' %<' " start truncating from here if the window gets too small
    let s .= '%=' " seperate right- from left-aligned
    let s .= '%l' " current line number
    let s .= ',%c' " column number
    let s .= ' of %L' " total line numbers
    let s .= ' %P' " Percentage through file
  "  let s .= "\n\n" 
    return s
endfunction
set statusline=%!MyStatusLine()

function! MyTabLine()
        let s = ''
        for i in range(tabpagenr('$'))
            " set up some oft-used variables
            let tab = i + 1 " range() starts at 0
            let winnr = tabpagewinnr(tab) " gets current window of current tab
            let buflist = tabpagebuflist(tab) " list of buffers associated with the windows in the current tab
            let bufnr = buflist[winnr - 1] " current buffer number
            let bufname = bufname(bufnr) " gets the name of the current buffer in the current window of the current tab

            let s .= '%' . tab . 'T' " start a tab
            let s .= (tab == tabpagenr() ? '%#TabLineSel#' : '%#TabLine#') " if this tab is the current tab...set the right highlighting
            let s .= ' #' . tab " current tab number
            let n = tabpagewinnr(tab,'$') " get the number of windows in the current tab
            if n > 1
                let s .= ':' . n " if there's more than one, add a colon and display the count
            endif
      let bufmodified = getbufvar(bufnr, "&mod")
            if bufmodified
                let s .= ' +'
            endif
            if bufname != ''
                let s .= ' ' . pathshorten(bufname) . ' ' " outputs the one-letter-path shorthand & filename
            else
                let s .= ' [No Name] '
            endif
        endfor
        let s .= '%#TabLineFill#' " blank highlighting between the tabs and the righthand close 'X'
        let s .= '%T' " resets tab page number?
        return s
endfunction
set tabline=%!MyTabLine()

" -----------------------------------------------------------------------------------------------}}}

" Scripting --------------------------------------------------------------------------------------{{{

"call log#init('ALL', ['~/.vim/vimlog.log'])

" -----------------------------------------------------------------------------------------------}}}

" vim: foldmethod=marker
