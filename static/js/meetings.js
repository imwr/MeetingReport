function getCookie(c_name) {
    if (document.cookie.length > 0) {
        var c_start = document.cookie.indexOf(c_name + "=");
        if (c_start != -1) {
            c_start = c_start + c_name.length + 1;
            var c_end = document.cookie.indexOf(";", c_start);
            if (c_end == -1) c_end = document.cookie.length;
            return unescape(document.cookie.substring(c_start, c_end));
        }
    }
    return "";
}
var messageTimeout = null;
function showmsg(msg, callback) {
    $("#send_email").removeAttr("disabled");
    clearTimeout(messageTimeout)
    var message = $("#message").addClass("open").find("div").html(msg || "Error").end()
    messageTimeout = setTimeout(function () {
        message.removeClass("open")
        callback && callback()
    }, 3000)
}
$(function () {
    $.ajaxSetup({
        headers: {"X-CSRFToken": getCookie("csrftoken")}
    });

    $("#send_email").on("click", function () {
        $(this).attr("disabled", 'disabled');
        var milestonedate1 = $("#milestonedate1").removeClass("border-red").val(),
            milestonedate2 = $("#milestonedate2").removeClass("border-red").val(),
            milestone1 = $("#milestone1").removeClass("border-red").val(),
            milestone2 = $("#milestone2").removeClass("border-red").val();
        if (!milestone1) {
            $("#milestone1").addClass("border-red")
            return showmsg("请填写里程碑内容");
        }
        if (!milestone2) {
            $("#milestone2").addClass("border-red")
            return showmsg("请填写下一里程碑内容");
        }
        var now = new Date().getTime();
        if (!milestonedate1) {
            $("#milestonedate1").addClass("border-red")
            return showmsg("请选择里程碑时间");
        }
        milestonedate1 = milestonedate1.substring(0, 10)
        if (new Date(milestonedate1).getTime() < now) {
            $("#milestonedate1").addClass("border-red")
            return showmsg("里程碑时间须大于当前时间");
        }
        milestonedate2 = milestonedate2.substring(0, 10)
        if (!milestonedate2) {
            $("#milestonedate2").addClass("border-red")
            return showmsg("请选择下一里程碑时间");
        }
        if (new Date(milestonedate2).getTime() < now) {
            $("#milestonedate2").addClass("border-red")
            return showmsg("下一里程碑时间须大于当前时间");
        }
        var reports = [];
        var reportareas = $("[id^='report-']").removeClass("border-red").each(function () {
            var value = this.value.replace(/\d\./g, '');
            if (!value) {
                return $(this).addClass("border-red")
            }
            reports.push({
                'user_id': $(this).attr("data-userid"),
                'username': $(this).attr("data-username"),
                'content': value == "leave" ? value : value.replace(/\n/g, ',')
            })
        })
        if (reports.length != reportareas.length) {
            return showmsg("请完善所有组员早会内容");
        }
        $.ajax({
            url: "/meeting-reports/send_email",
            type: "GET",
            data: {
                duty: $("#duty").val(),
                milestonedate1: milestonedate1,
                milestonedate2: milestonedate2,
                milestone1: milestone1,
                milestone2: milestone2,
                reports: JSON.stringify(reports)
            },
            success: function (data) {
                if (!data.success) {
                    return showmsg(data.msg)
                }
                showmsg('发送成功', function () {
                    location.href = "/meeting-reports/list"
                });
            },
            error: function (data) {
                showmsg(data.responseText);
            }
        })
    })

    $("textarea.autoheigth").on("input", function () { // 早会内容自动编号、高度扩展
        var orgins = this.value.replace(/ +/g, '').replace(/；|;/g, '').replace(/\d\./g, ''), value = '';
        if (!orgins) return
        var lines = orgins.split("\n");
        for (var index in lines) {
            if (!lines[index]) continue
            value += (Number(index) + 1) + "." + lines[index] + (index < lines.length - 1 ? "\n" : "")
        }
        this.value = value;
        this.style.height = 'auto';
        this.style.height = this.scrollHeight + 'px';
    }).trigger("input")

    $(".input-last").on("click", function () {// 获取上次早会内容
        var textarea = $(this).prev(), that = $(this);
        if (textarea.attr("disabled") == "disabled") return
        if (that.attr("data-content")) {
            return textarea.val($(this).attr("data-content").split(",").join("\n")).trigger("input");
        }
        var user = that.attr("data-user"),
            meeting = that.attr("data-meeting"),
            csrfmiddlewaretoken = $("[name=csrfmiddlewaretoken]").val();
        if (!user || !meeting || !csrfmiddlewaretoken) {
            return
        }
        $.ajax({
            url: "/meeting-reports/get_last_userreport?userid=" + user + "&meetingid=" + meeting + "&csrfmiddlewaretoken=" + csrfmiddlewaretoken,
            type: "GET",
            success: function (data) {
                textarea.val((data + "").split(",").join("\n")).trigger("input");
                that.attr("data-content", data)
            },
            error: function (data) {
                showmsg(data.responseText)
            }
        })
    })

    $(".leave-box").on("click", function () { // leave
        var user = $(this).attr("data-user"), dutyInput = $("#duty"), menbers = $("#menbers");
        var duty = dutyInput.val(); // 值日已经leave
        $("#report-" + user).val(this.checked ? "leave" : "").attr("disabled", this.checked).removeClass("border-red");
        menbers.find("span[data-user='" + user + "']").attr("data-leave", this.checked);
        !this.checked && ($("#send_email").removeAttr("disabled"))
        if (dutyInput.attr("data-duty") == user) {
            if (this.checked) { // 值日leave，选择下一个记录人
                var next = menbers.find(".text-red").removeClass("text-red").nextAll("span[data-leave=false]").eq(0)
                if (next.length > 0) {
                    next.addClass("text-red")
                } else {
                    next = menbers.find("span[data-leave=false]").eq(0).addClass("text-red")
                    if (next.length == 0) { // 全部leave了
                        $("#send_email").attr("disabled", "disabled")
                    }
                }
                dutyInput.val(next.attr("data-user")).prev("span").text(next.text() || "无");
            } else { // 值日未leave
                var curr = menbers.find(".text-red").removeClass("text-red").end()
                    .find("span[data-user='" + dutyInput.attr("data-duty") + "']").addClass("text-red");
                dutyInput.val("").prev("span").text(curr.text());
            }
        } else { // 非值日已被指定为值日
            var next = null;
            if (duty == user) {
                next = menbers.find(".text-red").removeClass("text-red").nextAll("span[data-leave=false]").eq(0)
            } else {
                menbers.find(".text-red").removeClass("text-red");
                next = menbers.find("span[data-user=" + dutyInput.attr("data-duty") + "]").nextAll("span[data-leave=false]").eq(0)
            }
            if (next.length > 0) {
                next.addClass("text-red")
            } else {
                next = menbers.find("span[data-leave=false]").eq(0).addClass("text-red")
                if (next.length == 0) { // 全部leave了
                    $("#send_email").attr("disabled", "disabled")
                }
            }
            dutyInput.val(next.attr("data-user")).prev("span").text(next.text() || "无");
        }
    })
})