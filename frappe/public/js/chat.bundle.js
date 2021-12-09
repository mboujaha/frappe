import "./frappe/chat";
//
// //
// const args = {
// 	filename: "somename.txt",
// 	doctype: "doctype",
// 	fieldname: "fieldname",
// 	docname: cur_frm.name,
// 	filedata: data,
// };
//
// frappe.call({
// 	"method": "uploadfile",
// 	args: args,
// 	callback: function (rr) {
// 		console.log(rr);
// 		if (!r._server_messages)
// 			msgbox.hide();
// 		if (r.exc) {
// 			// if no onerror, assume callback will handle errors
// 			opts.onerror ? opts.onerror :
// 				opts.callback(null, null, r);
// 			return;
// 		}
// 		var attachment = r.message;
// 		console.log(attachment)
// 		opts.callback(attachment, r);
// 		$(document).trigger("upload_complete",
// 			attachment
// 		);
// 	}
// });
//
//
// frappe.call({
// 	method: "frappe.client.get_list",
// 	args: {
// 		doctype: doctype,
// 		fields: fields,
// 		filters: filters
// 	},
// 	callback: function (res) {
// 	}
// });
