webpackJsonp([1],{"I6/8":function(e,t){},NHnr:function(e,t,r){"use strict";Object.defineProperty(t,"__esModule",{value:!0});var a=r("Xxa5"),n=r.n(a),s=r("exGp"),o=r.n(s),i=r("7+uW"),l=r("Lgyv"),u=r.n(l),c="http://localhost:3000",d="AuTuMN TB-modelling",m=!0,p=r("mvHQ"),v=r.n(p),f=r("M4fF"),h=r.n(f),w=r("0hgu"),g=r.n(w),_=r("BO1k"),b=r.n(_),x=function(e){return v()(e,null,2)},y=r("Gu7T"),k=r.n(y),P=r("mtWM"),S=r.n(P),C=r("lDdF"),R=r.n(C);S.a.defaults.withCredentials=!0;var U={rpcRun:function(e){for(var t=this,r=arguments.length,a=Array(r>1?r-1:0),s=1;s<r;s++)a[s-1]=arguments[s];return o()(n.a.mark(function r(){var s,o,i;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return o={method:e,params:a,jsonrpc:"2.0"},(s=console).log.apply(s,["> rpc.rpcRun",e].concat(k()(a))),t.prev=2,t.next=5,S.a.post(c+"/api/rpc-run",o);case 5:return i=t.sent,t.abrupt("return",i.data);case 9:return t.prev=9,t.t0=t.catch(2),t.abrupt("return",{error:{code:-32e3,message:t.t0.toString()}});case 12:case"end":return t.stop()}},r,t,[[2,9]])}))()},rpcUpload:function(e,t){for(var r=arguments.length,a=Array(r>2?r-2:0),s=2;s<r;s++)a[s-2]=arguments[s];var i=this;return o()(n.a.mark(function r(){var s,o,l,u,d,m,p,f,h;return n.a.wrap(function(r){for(;;)switch(r.prev=r.next){case 0:for((o=new FormData).append("method",e),o.append("params",v()(a)),o.append("jsonrpc","2.0"),l=!0,u=!1,d=void 0,r.prev=7,m=b()(t);!(l=(p=m.next()).done);l=!0)f=p.value,o.append("uploadFiles",f,f.name);r.next=15;break;case 11:r.prev=11,r.t0=r.catch(7),u=!0,d=r.t0;case 15:r.prev=15,r.prev=16,!l&&m.return&&m.return();case 18:if(r.prev=18,!u){r.next=21;break}throw d;case 21:return r.finish(18);case 22:return r.finish(15);case 23:return(s=console).log.apply(s,["> rpc.rpcUpoad",e,t].concat(k()(a))),r.prev=24,r.next=27,S.a.post(c+"/api/rpc-upload",o);case 27:return h=r.sent,r.abrupt("return",h.data);case 31:return r.prev=31,r.t1=r.catch(24),r.abrupt("return",{error:{code:-32e3,message:r.t1.toString()}});case 34:case"end":return r.stop()}},r,i,[[7,11,15,23],[16,,18,22],[24,31]])}))()},rpcDownload:function(e){for(var t=this,r=arguments.length,a=Array(r>1?r-1:0),s=1;s<r;s++)a[s-1]=arguments[s];return o()(n.a.mark(function r(){var s,o,i,l,u,d;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return o={method:e,params:a,jsonrpc:"2.0"},(s=console).log.apply(s,["> rpc.rpcDownload"].concat(k()(a))),t.prev=2,t.next=5,S.a.post(c+"/api/rpc-download",o);case 5:return i=t.sent,l=i.headers.filename,u=JSON.parse(i.headers.data),console.log("> rpc.rpcDownload response",u),u.error||(d=new Blob([i.data]),R.a.saveAs(d,l)),t.abrupt("return",u);case 13:return t.prev=13,t.t0=t.catch(2),t.abrupt("return",{error:{code:-32e3,message:t.t0.toString()}});case 16:case"end":return t.stop()}},r,t,[[2,13]])}))()}},$=r("NYxO");i.default.use($.a);var E=new $.a.Store({state:{user:{authenticated:!1}},mutations:{setUser:function(e,t){e.user=t}}});function j(e){var t=h.a.cloneDeep(e);return!t.password&&t.rawPassword&&(t.password=g()(t.rawPassword).toString(),delete t.rawPassword),t.rawPasswordConfirm&&delete t.rawPasswordConfirm,t}var G={login:function(e){var t=this;return o()(n.a.mark(function r(){var a,s,o;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return a=j(e),console.log("> auth.login",a),t.next=4,U.rpcRun("publicLoginUser",a);case 4:return s=t.sent,console.log("> auth.login response",s),s.result&&(o=h.a.cloneDeep(E.state.user),h.a.assign(o,s.result.user),o.authenticated=!0,o.password=a.password,localStorage.setItem("user",x(o)),E.commit("setUser",o)),t.abrupt("return",s);case 8:case"end":return t.stop()}},r,t)}))()},register:function(e){var t=j(e);return console.log("> auth.register",t),U.rpcRun("publicRegisterUser",t)},update:function(e){var t=this;return o()(n.a.mark(function r(){var a,s,o;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return a=j(e),console.log("> auth.update",x(a)),t.next=4,U.rpcRun("loginUpdateUser",a);case 4:return(s=t.sent).result&&(o=h.a.cloneDeep(E.state.user),h.a.assign(o,a),localStorage.setItem("user",v()(o)),E.commit("setUser",o)),t.abrupt("return",s);case 7:case"end":return t.stop()}},r,t)}))()},resetPassword:function(e,t){var r=this;return o()(n.a.mark(function a(){var s;return n.a.wrap(function(r){for(;;)switch(r.prev=r.next){case 0:return s=g()(t).toString(),console.log("> auth.resetPassword",e,s),r.abrupt("return",U.rpcRun("publicForceUpdatePassword",e,s));case 3:case"end":return r.stop()}},a,r)}))()},restoreLastUser:function(){var e=this;return o()(n.a.mark(function t(){var r;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:if(r=JSON.parse(localStorage.getItem("user")),console.log("> auth.restoreLastUser from localStorage",r),!r){t.next=4;break}return t.abrupt("return",e.login(r));case 4:case"end":return t.stop()}},t,e)}))()},logout:function(){return localStorage.removeItem("user"),E.commit("setUser",{authenticated:!1}),U.rpcRun("publicLogoutUser")}},L={name:"navbar",data:function(){return{title:d,isUser:m}},computed:{user:function(){return this.$store.state.user}},methods:{editUser:function(){this.$router.push("/edit-user")},home:function(){this.$router.push("/")},logout:function(){var e=this;return o()(n.a.mark(function t(){return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,G.logout();case 2:e.$router.push("/login");case 3:case"end":return t.stop()}},t,e)}))()}}},D={render:function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("md-toolbar",{staticClass:"md-dense"},[r("md-icon",{attrs:{"md-src":"./static/logo.png"}}),e._v(" "),r("h2",{staticClass:"md-title",staticStyle:{"padding-left":"1em",cursor:"pointer",flex:"1"},on:{click:function(t){e.home()}}},[e._v("\n    "+e._s(e.title)+"\n  ")]),e._v(" "),e.isUser?r("div",[e.user.authenticated?r("md-menu",[r("md-button",{attrs:{"md-menu-trigger":""}},[e._v("\n        "+e._s(e.user.name)+"\n      ")]),e._v(" "),r("md-menu-content",[r("md-menu-item",{on:{click:e.editUser}},[e._v("\n          Edit User\n        ")]),e._v(" "),r("md-menu-item",{on:{click:e.logout}},[e._v("\n          Logout\n        ")])],1)],1):r("router-link",{attrs:{to:"/login",tag:"md-button"}},[e._v("\n      Login\n    ")])],1):e._e()],1)},staticRenderFns:[]},F={name:"app",components:{Navbar:r("VU/8")(L,D,!1,null,null,null).exports}},M={render:function(){var e=this.$createElement,t=this._self._c||e;return t("div",{attrs:{id:"app"}},[t("navbar"),this._v(" "),t("router-view")],1)},staticRenderFns:[]};var N=r("VU/8")(F,M,!1,function(e){r("rpYJ")},null,null).exports,T=r("/ocq"),A=r("GDE4"),B=r.n(A),V=r("bm7V"),I=r.n(V);i.default.use(I.a);var O={name:"experiments",components:{vueSlider:B.a},data:function(){return{paramGroups:[],params:{},isRunning:!1,consoleLines:[],filenames:[],project:null,projects:[],paramGroup:null,iParamGroup:-1,width:50,imageStyle:"width: 50%"}},created:function(){var e=this;return o()(n.a.mark(function t(){var r;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return e.checkRun(),t.next=3,U.rpcRun("public_get_autumn_params");case 3:(r=t.sent).result&&(console.log("> Model.created",r.result),e.paramGroups=r.result.paramGroups,e.params=r.result.params,e.paramGroup=e.paramGroups[0],e.projects=r.result.projects);case 5:case"end":return t.stop()}},t,e)}))()},methods:{checkRun:function(){var e=this;return o()(n.a.mark(function t(){var r,a;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return t.next=2,U.rpcRun("public_check_autumn_run");case 2:(r=t.sent).result&&(e.consoleLines=r.result.console,e.$el.querySelector&&((a=e.$el.querySelector("#console-output")).scrollTop=a.scrollHeight)),r.result.is_running?(e.isRunning=!0,setTimeout(e.checkRun,2e3)):e.isRunning=!1;case 5:case"end":return t.stop()}},t,e)}))()},deleteBreakpoint:function(e,t,r){this.params[t].value.splice(r,1)},addBreakpoint:function(e,t){this.params[t].value.push(h.a.max(this.params[t].value))},breakpointCallback:function(e,t){},selectParamGroup:function(e){this.paramGroup=this.paramGroups[e]},run:function(){var e=this;return o()(n.a.mark(function t(){var r,a,s,o,i,l,u,d;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:for(r=h.a.cloneDeep(e.params),a=!0,s=!1,o=void 0,t.prev=4,i=b()(h.a.values(e.params));!(a=(l=i.next()).done);a=!0)"breakpoints"===(u=l.value).type&&(u.value=h.a.sortedUniq(u.value),console.log(x(u)));t.next=12;break;case 8:t.prev=8,t.t0=t.catch(4),s=!0,o=t.t0;case 12:t.prev=12,t.prev=13,!a&&i.return&&i.return();case 15:if(t.prev=15,!s){t.next=18;break}throw o;case 18:return t.finish(15);case 19:return t.finish(12);case 20:return e.filenames=[],e.isRunning=!0,e.project="",e.consoleLines=[],setTimeout(e.checkRun,2e3),t.next=27,U.rpcRun("public_run_autumn",r);case 27:(d=t.sent).result?(e.project=d.result.project,e.filenames=h.a.map(d.result.filenames,function(e){return c+"/file/"+e}),console.log(">> Model.run filenames",e.filenames)):(e.consoleLines.push("Error: model crashed"),e.isRunning=!1);case 29:case"end":return t.stop()}},t,e,[[4,8,12,20],[13,,15,19]])}))()},changeProject:function(e){var t=this;return o()(n.a.mark(function r(){var a;return n.a.wrap(function(r){for(;;)switch(r.prev=r.next){case 0:return console.log("> Model.changeProject",e),r.next=3,U.rpcRun("public_get_project_images",e);case 3:(a=r.sent).result&&(t.filenames=h.a.map(a.result.filenames,function(e){return c+"/file/"+e}),console.log(">> Model.changeProject filenames",t.filenames));case 5:case"end":return r.stop()}},r,t)}))()},changeWidth:function(e){console.log("> Model.changeWidth",e),this.imageStyle="width: "+this.width+"%",console.log("> Model.changeWidth",this.imageStyle)}}},W={render:function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("div",{},[r("md-layout",{attrs:{"md-column":""}},[r("md-layout",{attrs:{"md-row":""}},[r("md-layout",{staticStyle:{width:"50%",height:"calc(100vh - 48px)",overflow:"auto"},attrs:{"md-row":""}},[r("md-whiteframe",{staticStyle:{width:"230px","padding-top":"30px"}},[r("h2",{staticClass:"md-heading",staticStyle:{"padding-left":"15px"}},[e._v("\n            Parameter sets\n          ")]),e._v(" "),r("md-list",e._l(e.paramGroups,function(t,a){return r("md-list-item",{key:a,attrs:{id:t.name},on:{click:function(t){e.selectParamGroup(a)}}},[e._v("\n              "+e._s(t.name)+"\n            ")])}))],1),e._v(" "),r("md-whiteframe",{staticStyle:{width:"220px"}},[e.paramGroup?r("md-layout",{staticStyle:{padding:"30px 15px"},attrs:{"md-column":""}},[r("h2",{staticClass:"md-heading"},[e._v("\n              "+e._s(e.paramGroup.name)+"\n            ")]),e._v(" "),e._l(e.paramGroup.keys,function(t,a){return r("md-layout",{key:a,attrs:{"md-column":""}},["boolean"==e.params[t].type?r("div",[r("md-checkbox",{attrs:{type:"checkbox",tabindex:"0",id:t},model:{value:e.params[t].value,callback:function(r){e.$set(e.params[t],"value",r)},expression:"params[key].value"}},[e._v("\n                  "+e._s(e.params[t].label)+"\n                ")])],1):"drop_down"==e.params[t].type?r("div",[r("md-input-container",[r("label",[e._v(e._s(e.params[t].label))]),e._v(" "),r("md-select",{model:{value:e.params[t].value,callback:function(r){e.$set(e.params[t],"value",r)},expression:"params[key].value"}},e._l(e.params[t].options,function(t,a){return r("md-option",{key:a,attrs:{value:t}},[e._v("\n                      "+e._s(t)+"\n                    ")])}))],1)],1):"number"===e.params[t].type||"double"===e.params[t].type||"integer"===e.params[t].type?r("div",[r("md-input-container",[r("label",[e._v(e._s(e.params[t].label))]),e._v(" "),r("md-input",{attrs:{type:"number",step:"any"},model:{value:e.params[t].value,callback:function(r){e.$set(e.params[t],"value",r)},expression:"params[key].value"}})],1)],1):"slider"==e.params[t].type?r("div",[r("label",[e._v(e._s(e.params[t].label))]),e._v(" "),r("div",{staticStyle:{height:"2.5em"}}),e._v(" "),r("vue-slider",{attrs:{max:e.params[t].max,interval:e.params[t].interval},model:{value:e.params[t].value,callback:function(r){e.$set(e.params[t],"value",r)},expression:"params[key].value"}})],1):"breakpoints"==e.params[t].type?r("div",[r("label",[e._v(e._s(e.params[t].label))]),e._v(" "),r("div",{staticStyle:{height:"2.5em"}}),e._v(" "),e._l(e.params[t].value,function(a,n){return r("md-layout",{key:n,staticStyle:{width:"200px"},attrs:{"md-row":""}},[r("vue-slider",{staticStyle:{width:"130px"},attrs:{max:100,interval:1},on:{"drag-end":function(r){e.breakpointCallback(e.params,t)}},model:{value:e.params[t].value[n],callback:function(r){e.$set(e.params[t].value,n,r)},expression:"params[key].value[i]"}}),e._v(" "),r("md-button",{staticClass:"md-icon-button md-raised",on:{click:function(r){e.deleteBreakpoint(e.params,t,n)}}},[r("md-icon",[e._v("delete")])],1)],1)}),e._v(" "),r("md-button",{staticClass:"md-icon-button md-raised",on:{click:function(r){e.addBreakpoint(e.params,t)}}},[r("md-icon",[e._v("add")])],1)],2):e._e()])})],2):e._e()],1),e._v(" "),r("md-layout",{attrs:{"md-flex":""}},[r("div",{staticStyle:{width:"100%",padding:"30px 15px"}},[r("md-layout",{attrs:{"md-column":"","md-align":"start","md-vertical-align":"start"}},[r("h2",{staticClass:"md-heading"},[e._v("\n                Run model\n              ")]),e._v(" "),r("div",{staticStyle:{width:"100%"}},[r("md-layout",{attrs:{"md-row":"","md-vertical-align":"center"}},[r("md-button",{staticClass:"md-raised",attrs:{"md-flex":"true",disabled:e.isRunning},on:{click:function(t){e.run()}}},[e._v("\n                    Run\n                  ")]),e._v(" "),e.isRunning?r("md-spinner",{attrs:{"md-size":30,"md-indeterminate":""}}):e._e()],1)],1),e._v(" "),r("h2",{staticClass:"md-heading"},[e._v("\n                Console Output\n              ")]),e._v(" "),r("md-layout",{staticStyle:{width:"100%","background-color":"#EEE"}},[r("div",{staticStyle:{height:"350px","overflow-y":"scroll","font-family":"Courier, fixed","font-size":"0.9em"},attrs:{id:"console-output"}},e._l(e.consoleLines,function(t,a){return r("div",{key:a,staticStyle:{margin:"0 8px"}},[e._v("\n                    "+e._s(t)+"\n                  ")])}))]),e._v(" "),r("h2",{staticClass:"md-heading",staticStyle:{"margin-top":"1.5em"}},[e._v("\n                Graphs\n              ")]),e._v(" "),r("md-layout",{attrs:{"md-flex":"100","md-vertical-align":"center"}},[r("md-input-container",{staticStyle:{width:"200px"}},[r("label",[e._v("Existing Projects")]),e._v(" "),r("md-select",{on:{change:e.changeProject},model:{value:e.project,callback:function(t){e.project=t},expression:"project"}},e._l(e.projects,function(t,a){return r("md-option",{key:a,attrs:{value:t}},[e._v("\n                      "+e._s(t)+"\n                    ")])}))],1),e._v(" "),r("vue-slider",{staticStyle:{width:"500px"},attrs:{max:100,min:10,interval:1},on:{callback:function(t){e.changeWidth(e.width)}},model:{value:e.width,callback:function(t){e.width=t},expression:"width"}})],1),e._v(" "),r("md-layout",{staticStyle:{width:"100%"}},e._l(e.filenames,function(t,a){return r("md-card",{key:a,style:e.imageStyle},[r("md-card-media",[r("img",{staticStyle:{width:"100%"},attrs:{src:t}})])],1)}))],1)],1)])],1)],1)],1)],1)},staticRenderFns:[]};var J=r("VU/8")(O,W,!1,function(e){r("I6/8")},"data-v-1d77ebd2",null).exports,q={name:"Login",data:function(){return{title:d,email:"",rawPassword:"",error:""}},methods:{submit:function(){var e=this;return o()(n.a.mark(function t(){var r,a;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return r={email:e.$data.email,rawPassword:e.$data.rawPassword},console.log("> Login.submit",r),t.next=4,G.login(r);case 4:a=t.sent,console.log("> Login.submit response",a),a.result?e.$router.push("/"):e.error=a.error.message;case 7:case"end":return t.stop()}},t,e)}))()}}},H={render:function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("md-layout",{attrs:{"md-align":"center"}},[r("md-whiteframe",{staticStyle:{"margin-top":"4em",padding:"3em"}},[r("md-layout",{attrs:{"md-flex":"50","md-align":"center","md-column":""}},[r("h2",{staticClass:"md-display-2"},[e._v("\n        Login to "+e._s(e.title)+"\n      ")]),e._v(" "),r("form",{staticClass:"login-screen",attrs:{novalidate:""},on:{submit:function(t){return t.preventDefault(),e.submit(t)}}},[r("md-input-container",[r("label",[e._v("E-mail address")]),e._v(" "),r("md-input",{attrs:{type:"text",placeholder:"E-mail address"},model:{value:e.email,callback:function(t){e.email=t},expression:"email"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("Password")]),e._v(" "),r("md-input",{attrs:{type:"password",placeholder:"Password"},model:{value:e.rawPassword,callback:function(t){e.rawPassword=t},expression:"rawPassword"}})],1),e._v(" "),r("md-button",{staticClass:"md-raised md-primary",attrs:{type:"submit"}},[e._v("login")]),e._v(" "),e.error?r("div",{staticStyle:{color:"red"}},[e._v("\n          "+e._s(e.error)+"\n        ")]):e._e(),e._v(" "),r("div",{staticStyle:{"margin-top":"3em"}},[e._v("\n          New to "+e._s(e.title)+"?  \n          "),r("router-link",{attrs:{to:"/register"}},[e._v("Register")])],1)],1)])],1)],1)},staticRenderFns:[]},Y=r("VU/8")(q,H,!1,null,null,null).exports,z={name:"Register",data:function(){return{title:d,name:"",email:"",rawPassword:"",rawPasswordConfirm:"",user:G.user,error:""}},methods:{submit:function(){var e=this;return o()(n.a.mark(function t(){var r,a;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:return r={name:e.$data.name,email:e.$data.email,rawPassword:e.$data.rawPassword,rawPasswordConfirm:e.$data.rawPasswordConfirm},t.next=3,G.register(r);case 3:if(!(a=t.sent).result){t.next=9;break}return console.log("> Register.submit register success",a.result),t.next=8,G.login({email:r.email,rawPassword:r.rawPassword});case 8:a=t.sent;case 9:a.result?(console.log("> Register.submit login success",a.result),e.$router.push("/")):(console.log("> Register.submit fail",a.error),e.error=a.error.message);case 10:case"end":return t.stop()}},t,e)}))()}}},Q={render:function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("md-layout",{attrs:{"md-align":"center"}},[r("md-whiteframe",{staticStyle:{"margin-top":"4em",padding:"3em"}},[r("md-layout",{attrs:{"md-flex":"50","md-align":"center","md-column":""}},[r("h2",{staticClass:"md-display-2"},[e._v("\n        Register to "+e._s(e.title)+"\n      ")]),e._v(" "),r("form",{on:{submit:function(t){return t.preventDefault(),e.submit(t)}}},[r("md-input-container",[r("label",[e._v("User name")]),e._v(" "),r("md-input",{attrs:{type:"text",placeholder:"User name"},model:{value:e.name,callback:function(t){e.name=t},expression:"name"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("E-mail address")]),e._v(" "),r("md-input",{attrs:{type:"text",placeholder:"E-mail address"},model:{value:e.email,callback:function(t){e.email=t},expression:"email"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("Password")]),e._v(" "),r("md-input",{attrs:{type:"password",placeholder:"Password"},model:{value:e.rawPassword,callback:function(t){e.rawPassword=t},expression:"rawPassword"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("Confirm Password")]),e._v(" "),r("md-input",{attrs:{type:"password",placeholder:"Confirm Password"},model:{value:e.rawPasswordConfirm,callback:function(t){e.rawPasswordConfirm=t},expression:"rawPasswordConfirm"}})],1),e._v(" "),r("md-button",{staticClass:"md-raised md-primary",attrs:{type:"submit"}},[e._v("\n          Register\n        ")]),e._v(" "),e.error?r("div",{staticStyle:{color:"red"}},[e._v("\n          "+e._s(e.error)+"\n        ")]):e._e()],1)])],1)],1)},staticRenderFns:[]},X=r("VU/8")(z,Q,!1,null,null,null).exports,K={name:"EditUser",data:function(){var e={};return h.a.assign(e,this.$store.state.user),h.a.assign(e,{title:"Edit Your Details",rawPassword:"",rawPasswordConfirm:"",error:""}),e},methods:{submit:function(){var e=this;return o()(n.a.mark(function t(){var r,a,s,o,i,l,u,c,d;return n.a.wrap(function(t){for(;;)switch(t.prev=t.next){case 0:for(e.error="",r={},a=["id","name","email","rawPassword","rawPasswordConfirm"],s=!0,o=!1,i=void 0,t.prev=6,l=b()(a);!(s=(u=l.next()).done);s=!0)c=u.value,e.$data[c]&&(r[c]=e.$data[c]);t.next=14;break;case 10:t.prev=10,t.t0=t.catch(6),o=!0,i=t.t0;case 14:t.prev=14,t.prev=15,!s&&l.return&&l.return();case 17:if(t.prev=17,!o){t.next=20;break}throw i;case 20:return t.finish(17);case 21:return t.finish(14);case 22:return t.next=24,G.update(r);case 24:(d=t.sent).result?e.error="User updated":(console.log("> EditUser.submit fail",d),e.error=d.error.message);case 26:case"end":return t.stop()}},t,e,[[6,10,14,22],[15,,17,21]])}))()}}},Z={render:function(){var e=this,t=e.$createElement,r=e._self._c||t;return r("md-layout",{attrs:{"md-align":"center"}},[r("md-whiteframe",{staticStyle:{"margin-top":"4em",padding:"3em"}},[r("md-layout",{attrs:{"md-flex":"50","md-align":"center","md-column":""}},[r("h2",{staticClass:"md-display-2"},[e._v("\n        "+e._s(e.title)+"\n      ")]),e._v(" "),r("form",{on:{submit:function(t){return t.preventDefault(),e.submit(t)}}},[r("md-input-container",[r("label",[e._v("User name")]),e._v(" "),r("md-input",{attrs:{type:"text",placeholder:"User name"},model:{value:e.name,callback:function(t){e.name=t},expression:"name"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("E-mail address")]),e._v(" "),r("md-input",{attrs:{type:"text",placeholder:"E-mail address"},model:{value:e.email,callback:function(t){e.email=t},expression:"email"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("New Password")]),e._v(" "),r("md-input",{attrs:{type:"password",placeholder:"New Password"},model:{value:e.rawPassword,callback:function(t){e.rawPassword=t},expression:"rawPassword"}})],1),e._v(" "),r("md-input-container",[r("label",[e._v("Confirm Password")]),e._v(" "),r("md-input",{attrs:{type:"password",placeholder:"Confirm Password"},model:{value:e.rawPasswordConfirm,callback:function(t){e.rawPasswordConfirm=t},expression:"rawPasswordConfirm"}})],1),e._v(" "),r("md-button",{staticClass:"md-raised md-primary",attrs:{type:"submit"}},[e._v("\n          Save\n        ")]),e._v(" "),e.error?r("div",{staticStyle:{color:"red"}},[e._v("\n          "+e._s(e.error)+"\n        ")]):e._e()],1)])],1)],1)},staticRenderFns:[]},ee=r("VU/8")(K,Z,!1,null,null,null).exports;i.default.use(T.a);var te,re=new T.a({routes:[{path:"/",name:"model",component:J},{path:"/login",name:"login",component:Y},{path:"/register",name:"register",component:X},{path:"/edit-user",name:"editUser",component:ee}]}),ae=(te=o()(n.a.mark(function e(){return n.a.wrap(function(e){for(;;)switch(e.prev=e.next){case 0:if(!m){e.next=3;break}return e.next=3,G.restoreLastUser();case 3:return e.abrupt("return",new i.default({el:"#app",router:re,store:E,template:"<App/>",components:{App:N}}));case 4:case"end":return e.stop()}},e,this)})),function(){return te.apply(this,arguments)});i.default.config.productionTip=!1,i.default.use(u.a),i.default.material.registerTheme("default",{primary:"black"}),document.title=d,ae()},rpYJ:function(e,t){}},["NHnr"]);
//# sourceMappingURL=app.0f665a03e76a4a3637d9.js.map